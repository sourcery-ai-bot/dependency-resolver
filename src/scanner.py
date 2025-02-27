import os
from typing import Tuple
import typing
from clang.cindex import TranslationUnit, Index
from global_logger import Log

class DependencyScanner:

    SUPPORTED_FILES = [".cpp", ".c", ".hpp", ".h"]

    glob_log: Log = Log.get_logger(name="DepdendencyScanner", logs_dir=os.path.abspath("./log"))

    def __init__(self, progress_cb: typing.Callable[[int, int, str], None] = None) -> None:
        self.cindex = Index.create()
        self.__progress_cb = progress_cb

    @staticmethod
    def normalize_path(path:str) -> str:
        return path.replace("\\", "/")
    
    def is_valid_project_file(self, filename:str) -> int:
        """ Returns index that represents a file extension
        from SUPPORTED_FILES.
        """
        return next(
            (
                i
                for i, ext in enumerate(self.SUPPORTED_FILES)
                if filename.endswith(ext)
            ),
            -1,
        )

    def get_project_files(self, start_dir:str) -> list[Tuple[str, int]]:
        project_files = []

        for root, dirs, files in os.walk(start_dir):
            for path in files:
                file_type = self.is_valid_project_file(path)
                if file_type!=-1:                    
                    project_files.append((os.path.join(root,path), file_type))

        return project_files

    def get_includes(self, path:str) -> list[str]:

        self.glob_log.info(f"Parsing {path}")

        translation_unit = self.cindex.parse(
            path, 
            options = TranslationUnit.PARSE_SKIP_FUNCTION_BODIES | TranslationUnit.PARSE_INCOMPLETE
        )

        return [
            DependencyScanner.normalize_path(str(incl.include)) for incl in translation_unit.get_includes()
            if incl.depth == 1
        ]

    def scan_dir(self, path_dir:str) -> dict[str, list[str]]:
        """ Scans all supported files starting from path_dir
        including subdirectories.
        Returns: Dictionary with key being project file and value is
        a list of its dependencies.
        """

        path_dir = DependencyScanner.normalize_path(path_dir) 

        self.glob_log.info(f"Scan started {path_dir}")

        dep_map = {}
        project_files = self.get_project_files(path_dir)

        for i, (file, file_type) in enumerate(project_files):

            file = DependencyScanner.normalize_path(file)

            # Report progress to the caller
            if self.__progress_cb:
                self.__progress_cb(i, len(project_files), file.replace(path_dir, ""))

            includes = self.get_includes(file)
            dep_map[file] = includes

        self.glob_log.info("Scan complete!")

        return dep_map
    