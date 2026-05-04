from abc import ABC, abstractmethod


class Command(ABC):
    """Abstract interface for executable CLI commands.

    Decouples command logic from routing/orchestration, allowing
    commands to be composed, tested, and reused independently.
    """

    @abstractmethod
    def execute(self) -> None:
        """Execute the command.

        Raises:
            SystemExit: With appropriate exit code on error or request.
        """
