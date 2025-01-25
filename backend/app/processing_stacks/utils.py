#def get_language_from_extension(file_extension: str) -> str | None:
#    """Map file extension to tree-sitter language name"""
#    extension_to_language = {
#        # Web Technologies
#        ".js": "javascript",
#        ".jsx": "javascript",
#        ".ts": "typescript",
#        ".tsx": "typescript",
#        ".html": "html",
#        ".css": "css",
#        
#        # Systems Programming
#        ".c": "c",
#        ".h": "c",
#        ".cpp": "cpp",
#        ".hpp": "cpp",
#        ".cc": "cpp",
#        ".cxx": "cpp",
#        ".rs": "rust",
#        ".go": "go",
#        
#        # JVM Languages
#        ".java": "java",
#        ".scala": "scala",
#        ".kt": "kotlin",
#        
#        # .NET Languages
#        ".cs": "c_sharp",
#        
#        # Scripting Languages
#        ".py": "python",
#        ".rb": "ruby",
#        ".php": "php",
#        ".pl": "perl",
#        ".sh": "bash",
#        ".bash": "bash",
#        ".lua": "lua",
#        ".r": "r",
#        ".jl": "julia",
#        
#        # Query Languages
#        ".sql": "sql",
#        ".sqlite": "sql",
#        ".graphql": "ql",
#        ".gql": "ql",
#        
#        # Configuration & Data
#        ".json": "json",
#        ".yaml": "yaml",
#        ".yml": "yaml",
#        ".toml": "toml",
#        ".hcl": "hcl",
#        ".dockerfile": "dockerfile",
#        ".mod": "go_mod",
#        
#        # Functional Languages
#        ".hs": "haskell",
#        ".ml": "ocaml",
#        ".mli": "ocaml",
#        ".ex": "elixir",
#        ".exs": "elixir",
#        ".elm": "elm",
#        ".cl": "commonlisp",
#        ".lisp": "commonlisp",
#        ".el": "elisp",
#        
#        # Scientific Computing
#        ".f90": "fortran",
#        ".f95": "fortran",
#        ".f03": "fortran",
#        ".f08": "fortran",
#        ".f": "fixed_form_fortran",
#        ".for": "fixed_form_fortran",
#        ".f77": "fixed_form_fortran",
#        
#        # Mobile Development
#        ".swift": "swift",
#        ".m": "objc",
#        ".mm": "objc",
#        
#        # Other
#        ".erl": "erlang",
#        ".hack": "hack",
#        ".dot": "dot",
#        ".makefile": "make",
#        ".mk": "make",
#    }
#    return extension_to_language.get(file_extension.lower())