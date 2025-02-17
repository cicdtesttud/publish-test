#!/bin/bash

function parse_flags {
    compiler=$1
    compilerinfo=$2

    if [ $compiler = "clang" ]; then
        regex='"-target-feature" "\+([^\"]+)"'
        if [[ $compilerinfo =~ $regex ]] ; then
            flag="${BASH_REMATCH[1]}"
            printf "$flag "
            # Remove the first regex match and parse recursively
            parse_flags "$compiler" "${compilerinfo/${BASH_REMATCH[0]}/}"
        fi
    elif [ $compiler = "gcc" ]; then
        regex=' -m([^ ]+)'
        if [[ $compilerinfo =~ $regex ]] ; then
            flag="${BASH_REMATCH[1]}"
            # only print flags that do not start with "no-", since g++ explicitly emits unsupported flags this way.
            if [[ $flag != no-* ]]; then
                printf "$flag "
            fi
            # Remove the first regex match and parse recursively
            parse_flags "$compiler" "${compilerinfo/${BASH_REMATCH[0]}/}"
        fi
    else
        echo "Unknown compiler."
        exit -1
    fi
}

lscpu_exe=$(which lscpu 2>/dev/null)
if [[ ! -z ${lscpu_exe} && -f $lscpu_exe && -x $lscpu_exe ]]; then 
    flags=$(eval LANG=en;lscpu|grep -i flags | tr ' ' '\n' | grep -v -E '^Flags:|^$' | sort -d | tr '\n' ' ')
    echo "$flags"
else
    flag_set=()

    gcc_exe=$(which g++)
    clang_exe=$(which clang)

    if [[ -f $gcc_exe && -x $gcc_exe ]]; then
        gcc_output=$(eval $gcc_exe -E - -march=native -### 2>&1)
	      parsed_flags=$(parse_flags "gcc" "$gcc_output" | sed "s/\./_/g")

        # Parse whitespace-separated string into an array
        IFS=' ' read -r -a parsed_array <<< "$parsed_flags"
        unset IFS

        # Check for every flag if it is already contained in the flag array
        for flag in "${parsed_array[@]}"
        do
            if [[ ! " ${flag_set[*]} " =~ [[:space:]]${flag}[[:space:]] ]]; then
                flag_set+=("$flag")
            fi
        done
    fi

    if [[ -f $clang_exe && -x $clang_exe ]]; then
        if [[ "$OSTYPE" == "linux-gnu"* ]];  then
            if [[ $(uname -i) != aarch* && $(uname -i) != arm*  ]]; then
                arch_string="-march=native"
            else
                arch_string="-mcpu=native"
            fi
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            if [[ $(uname -m) != aarch* && $(uname -m) != arm*  ]]; then
                arch_string="-march=native"
            else
                arch_string="-mcpu=native"
            fi
        elif [[ "$OSTYPE" == "cygwin" ]]; then
            # POSIX compatibility layer and Linux environment emulation for Windows
            continue
        elif [[ "$OSTYPE" == "msys" ]]; then
            # Lightweight shell and GNU utilities compiled for Windows (part of MinGW)
            continue
        else
            echo "Could not detect the current operating system. Aborting."
            # exit 1
        fi

        clang_output=$(eval $clang_exe -E - $arch_string -### 2>&1)
        parsed_flags=$(parse_flags "clang" "$clang_output" | sed "s/\./_/g")

        # Parse whitespace-separated string into an array
        IFS=' ' read -r -a parsed_array <<< "$parsed_flags"
        unset IFS

        # Check for every flag if it is already contained in the flag array
        for flag in "${parsed_array[@]}"
        do
            if [[ ! " ${flag_set[*]} " =~ [[:space:]]${flag}[[:space:]] ]]; then
                flag_set+=("$flag")
            fi
        done
    fi
    
    if [ -z "{flag_set}" ]; then
      echo "Could not determine any flags"
      exit 1
    fi
    
    IFS=$'\n' sorted=($(sort <<<"${flag_set[*]}"))
    unset IFS
    printf "%s " "${sorted[@]}"
    printf "\n"
fi
