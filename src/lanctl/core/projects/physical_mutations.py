"""Apply VLF policy after an application operation releases its physical locks."""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from functools import wraps
from pathlib import Path

from lanctl.core.project_context import project_operation


@dataclass
class _Mutation:
    path: Path
    changed: bool = False


_mutation = ContextVar("lanctl_physical_mutation", default=None)


class PhysicalSaveError(RuntimeError):
    """The working inventory was committed, but its VLF could not be saved."""


def record_physical_write(path):
    """Only mark this operation's writes; never take a save lock here."""
    current = _mutation.get()
    if current is not None and Path(path).resolve() == current.path:
        current.changed = True


@contextmanager
def physical_mutation(path):
    """Group nested edits and keep the original project through the final save."""
    if _mutation.get() is not None:
        yield _mutation.get()
        return
    from lanctl.core.config import load_config
    from lanctl.core.paths import application_path
    from lanctl.core.projects.physical import workspace_path

    with project_operation():
        settings = load_config()
        workspace = settings.get("projectWorkspace")
        target = application_path(path).resolve()
        if (
            not settings.get("activeProject")
            or not isinstance(workspace, dict)
            or not workspace.get("database")
            or target != workspace_path(Path(workspace["database"])).resolve()
            or target != application_path(settings["physicalDatabase"]).resolve()
        ):
            # An explicit external/legacy database does not belong to this VLF.
            yield
            return
        current = _Mutation(target)
        token = _mutation.set(current)
        failed = False
        try:
            yield current
        except BaseException:
            failed = True
            raise
        finally:
            _mutation.reset(token)
            if current.changed:
                from lanctl.core.projects.save_policy import SaveTrigger, save_active_project

                try:
                    save_active_project(SaveTrigger.CHANGE, config=settings)
                except Exception as error:
                    from lanctl.core.errors import errors

                    event = errors.from_exception(
                        error,
                        origin="LANCTL.Project.Physical.Autosave",
                        code="PROJECT.PHYSICAL.AUTOSAVE_FAILED",
                        level=43,
                        details={
                            "project": settings["activeProject"],
                            "physicalDatabase": str(target),
                            "changesCommitted": True,
                        },
                        print_output=False,
                        break_execution=False,
                    )
                    if not failed:
                        raise PhysicalSaveError(
                            "Cambios aplicados a la base de trabajo, pero no se pudo guardar "
                            f"el VLF. No repitas la edición; reintenta el guardado. "
                            f"[{event.error_id}] {error}"
                        ) from error


def physical_edit(method):
    """Application services expose their physical store as ``self.database``."""

    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with physical_mutation(self.database.path):
            return method(self, *args, **kwargs)

    return wrapped
