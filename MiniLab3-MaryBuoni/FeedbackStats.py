"""
FeedbackStats.py
Model class that tracks customer satisfaction metrics for QuickRate kiosk.
Author: buonma98
"""

from Log import Log


class FeedbackStats:
    """
    FeedbackStats maintains customer feedback counts, calculates satisfaction
    percentages, and evaluates whether customer satisfaction has dropped below
    a configurable alert threshold (30%).
    """

    def __init__(self, threshold: float = 30.0, minVotes: int = 1):
        """
        Initialize satisfaction metrics.

        Parameters:
        -----------
        threshold : float
            Satisfaction percentage below which an alarm condition is triggered.
            Defaults to 30.0%.
        minVotes : int
            Minimum number of votes required before evaluating threshold.
            Defaults to 1.
        """
        self._positiveCount: int = 0
        self._negativeCount: int = 0
        self._threshold: float = threshold
        self._minVotes: int = minVotes
        Log.i(f"FeedbackStats initialized with threshold {threshold}% (min votes: {minVotes})")

    @property
    def positiveCount(self) -> int:
        """Return the count of positive feedback ratings."""
        return self._positiveCount

    @property
    def negativeCount(self) -> int:
        """Return the count of negative feedback ratings."""
        return self._negativeCount

    def recordPositive(self) -> None:
        """Increment positive feedback counter."""
        self._positiveCount += 1
        Log.i(f"FeedbackStats: +1 Positive. Pos={self._positiveCount}, Neg={self._negativeCount}, Score={self.getSatisfaction():.1f}%")

    def recordNegative(self) -> None:
        """Increment negative feedback counter."""
        self._negativeCount += 1
        Log.i(f"FeedbackStats: +1 Negative. Pos={self._positiveCount}, Neg={self._negativeCount}, Score={self.getSatisfaction():.1f}%")

    def getSatisfaction(self) -> float:
        """
        Calculate and return current satisfaction rate as a percentage (0.0 to 100.0).
        If no votes have been cast yet, returns 100.0%.
        """
        total = self._positiveCount + self._negativeCount
        if total == 0:
            return 100.0
        return round((self._positiveCount / total) * 100.0, 1)

    def belowThreshold(self) -> bool:
        """
        Check if satisfaction is below the alert threshold (default 30%).
        Only triggers if at least minVotes have been recorded.
        """
        total = self._positiveCount + self._negativeCount
        if total < self._minVotes:
            return False
        return self.getSatisfaction() < self._threshold

    def reset(self) -> None:
        """Reset all feedback statistics to 0."""
        self._positiveCount = 0
        self._negativeCount = 0
        Log.i("FeedbackStats: Reset statistics to 0")
