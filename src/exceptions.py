"""Custom exceptions for SmartPick AI data ingestion and validation."""


class SmartPickError(Exception):
    """Base exception for all SmartPick AI errors."""


class DatasetNotFoundError(SmartPickError):
    """Raised when the specified dataset file path does not exist."""

    def __init__(self, filepath: str) -> None:
        super().__init__(
            f"Dataset file not found at path: '{filepath}'. Please check the configuration."
        )
        self.filepath = filepath


class EmptyDatasetError(SmartPickError):
    """Raised when the dataset file contains no records (0 rows or headers only)."""

    def __init__(self, filepath: str) -> None:
        super().__init__(
            f"Dataset at '{filepath}' is completely empty. At least 1 record is required."
        )
        self.filepath = filepath


class MissingRequiredColumnError(SmartPickError):
    """Raised when required schema columns are missing from the dataset."""

    def __init__(
        self, missing_columns: list[str], available_columns: list[str]
    ) -> None:
        self.missing_columns = missing_columns
        self.available_columns = available_columns
        msg = (
            f"Dataset is missing required canonical column(s): {missing_columns}. "
            f"Available columns found: {available_columns}."
        )
        super().__init__(msg)


class MalformedDataError(SmartPickError):
    """Raised when CSV structure is corrupt or unparseable."""

    def __init__(
        self, message: str, original_exception: Exception | None = None
    ) -> None:
        super().__init__(message)
        self.original_exception = original_exception


class InvalidBudgetRangeError(SmartPickError):
    """Raised when budget bounds are invalid (min > max or negative)."""

    def __init__(self, min_budget: float, max_budget: float) -> None:
        super().__init__(
            f"Invalid budget interval [₹{min_budget:,.0f}, ₹{max_budget:,.0f}]. "
            "Minimum budget cannot exceed maximum budget, and bounds must be non-negative."
        )
        self.min_budget = min_budget
        self.max_budget = max_budget


class InvalidWeightsError(SmartPickError):
    """Raised when user preference weights are negative or all zero."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class NoEligiblePhonesError(SmartPickError):
    """Raised when filters return zero candidate phones."""

    def __init__(
        self,
        budget_min: float,
        budget_max: float,
        brands: list[str] | None = None,
        has_5g: bool | None = None,
    ) -> None:
        filter_parts = [f"Budget: ₹{budget_min:,.0f} - ₹{budget_max:,.0f}"]
        if brands:
            filter_parts.append(f"Brands: {', '.join(brands)}")
        if has_5g is not None:
            filter_parts.append(f"5G: {'Required' if has_5g else '4G Only'}")
        super().__init__(
            f"No smartphones found matching criteria ({'; '.join(filter_parts)}). "
            "Try broadening budget bounds or clearing brand filters."
        )


# Aliases for compatibility
BudgetValidationError = InvalidBudgetRangeError
ZeroWeightsError = InvalidWeightsError
