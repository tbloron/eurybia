"""
Common functions used in report
"""

import os
from enum import Enum
from numbers import Number
from typing import Callable, Dict, Optional, Union

import pandas as pd

# from pandas.api.types import is_bool_dtype, is_categorical_dtype, is_numeric_dtype, is_string_dtype
from pandas.api.types import infer_dtype, is_numeric_dtype


class VarType(Enum):
    """
    Helper class to indicate the type of a variable.
    """

    TYPE_CAT = "Categorical"
    TYPE_NUM = "Numeric"
    TYPE_UNSUPPORTED = "Unsupported"

    def __str__(self) -> str:
        return str(self.value)


def display_value(value: float, thousands_separator: str = ",", decimal_separator: str = ".") -> str:
    """
    Display a value as a string with specific format.
    Parameters
    ----------
    value : float
        Value to display.
    thousands_separator : str
        The separator used to separate thousands.
    decimal_separator : str
        The separator used to separate decimal values.
    Returns
    -------
    str
    Examples
    --------
    >>> display_value(1255000, thousands_separator=',')
    '1,255,000'
    """
    value_str = f"{value:,}".replace(",", "/thousands/").replace(".", "/decimal/")
    return value_str.replace("/thousands/", thousands_separator).replace("/decimal/", decimal_separator)


def replace_dict_values(obj: Dict, replace_fn: Callable, *args) -> dict:
    """
    Recursively iterates over all values of obj and changes its values using the replace_fn
    Parameters
    ----------
    obj : dict
    replace_fn : callable
    Returns
    -------
    dict
    """
    for k, value in obj.items():
        if isinstance(value, dict):
            obj[k] = replace_dict_values(value, replace_fn)
        elif isinstance(value, Number):
            obj[k] = replace_fn(value, *args)
    return obj


def series_dtype(s: pd.Series) -> VarType:
    """
    Computes the type of a pandas series.
    Parameters
    ----------
    s : pd.Series
        The series for which we wish to determine the type.
    Returns
    -------
    VarType
    """
    if infer_dtype(s) == "boolean":
        return VarType.TYPE_CAT
    elif infer_dtype(s, skipna=True) == "string":
        return VarType.TYPE_CAT
    elif isinstance(s.dtype, pd.CategoricalDtype):
        return VarType.TYPE_CAT
    elif is_numeric_dtype(s):
        if numeric_is_continuous(s):
            return VarType.TYPE_NUM
        else:
            return VarType.TYPE_CAT
    else:
        return VarType.TYPE_UNSUPPORTED


def numeric_is_continuous(s: pd.Series):
    """
    Function that returns True if a
    numeric pandas series is continuous and False if it is categorical.
    Parameters
    ----------
    s : pd.Series
    Returns
    -------
    bool
    """
    # This test could probably be improved
    n_unique = s.nunique()
    return True if n_unique > 15 else False


def get_callable(path: str):
    """
    This function is similar to the _locate function in Hydra library
    Locate an object by name or dotted path, importing as necessary.
    """
    if path == "":
        raise ImportError("Empty path")
    import builtins
    from importlib import import_module

    parts = [part for part in path.split(".") if part]
    module = None
    for number in reversed(range(len(parts))):
        try:
            mod = ".".join(parts[:number])
            module = import_module(mod)
        except Exception as e:
            if number == 0:
                raise ImportError(f"Error loading module '{path}'") from e
            continue
        if module:
            break
    if module:
        obj = module
    else:
        obj = builtins
    for part in parts[number:]:
        mod = mod + "." + part
        if not hasattr(obj, part):
            try:
                import_module(mod)
            except Exception as e:
                raise ImportError(f"Encountered error: `{e}` when loading module '{path}'") from e
        obj = getattr(obj, part)
    if isinstance(obj, type):
        obj_type: type = obj
        return obj_type
    elif callable(obj):
        obj_callable = obj
        return obj_callable
    else:
        # dummy case
        raise ValueError(f"Invalid type ({type(obj)}) found for {path}")


def compute_col_types(df_all: Optional[pd.DataFrame]) -> Dict:
    """
    Computes the type of each column and stores the result in a dict.
    Parameters
    ----------
    df_all : pd.DataFrame, optional
    Returns
    -------
    col_types : dict
        The types of each column
    """
    if df_all is None:
        return {}
    return {col: series_dtype(df_all[col]) for col in df_all.columns}


def load_saved_df(path: str) -> Union[pd.DataFrame, None]:
    """
    Loads a pandas DataFrame that was saved using pd.to_csv method.
    Parameters
    ----------
    path : str
        Path to the dataframe object
    Returns
    -------
    pd.DataFrame or None
    """
    if os.path.exists(path):
        return pd.read_pickle(path)

    else:
        return None
