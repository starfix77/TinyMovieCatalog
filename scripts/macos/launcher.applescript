on openCatalog()
    set homeFolder to POSIX path of (path to home folder)
    set controlScript to homeFolder & "Library/Application Support/TinyMovieCatalog/control.sh"
    try
        do shell script "/bin/bash " & quoted form of controlScript & " open"
    on error errorMessage
        display alert "TinyMovieCatalog" message errorMessage as critical
    end try
end openCatalog

on run
    openCatalog()
end run

on reopen
    openCatalog()
end reopen

on idle
    return 60
end idle
