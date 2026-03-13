
- Docstrings
    - Don't remove unless completely unnecessary after proposed changes
- Typehinting
    - Always typehint method parameters and return values, except for when the return value is None.
    - Prefer infering types in class attributes from default values, such as specifying the dtype of numpy arrays,
    - value simplicity over completeness. Example: if methods can accept a tuple or numpy array of either integers or floats. Let's just go with np.arraylike there.
    - Consistency is key: let's define types (and methods of nessecary) such that types are consistent across similar methods in classes.
