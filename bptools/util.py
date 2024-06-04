class FromSeriesMixin(object):
    """Utility mixin to add a class method to generate a new instance from a
    :class:`pd.Series`. This provides a single class method :meth:`from_series`.

    """
    @classmethod
    def from_series(cls, s):
        """Create a new instance using the provided series. The series must have
        labels that match arguments provided to the class on instantiation.

        """
        kwargs = {
            attr: value
            for attr, value in s.items()
        }
        return cls(**kwargs)


def standardize_label(label):
    """ Utility function to standardize a contact label

    Given either a monopolar or bipolar contact label returns the label in a standardized format:
        1. All uppercase characters
        2. No whitespace
        3. No leading zeros for lead numbers

    Parameters
    ----------
    label: str
        The contact label to be standardized

    Returns
    -------
    final_label: str
        The standardized contact label

    Notes
    -----
    Makes it easier to compare labels across different sources when they are stored consistently

    """
    # Update type of label to be string. Occasionally, pandas will infer a long
    # type for contacts starting with numbers
    label = str(label)

    # Remove whitepsace characters
    label = ''.join(label.split())

    # Use recursion for bipolars
    if label.find("-") != -1:
        tokens = label.split("-")
        left = standardize_label(tokens[0])
        right = standardize_label(tokens[1])
        return "-".join([left, right])

    final_label = label

    # Some contacts have a leading 0 (LAD01), so remove it
    if len(label)>1:
	if label[-2] == "0":
		final_label = label[:-2] + label[-1]

    # All characters should be uppercase 
    final_label = final_label.upper()

    return final_label
