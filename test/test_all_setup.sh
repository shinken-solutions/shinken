#!/bin/bash

STOP_ON_FAILURE=0

DISTRO=$(lsb_release -i | cut -f 2 | tr [A-Z] [a-z])

if [[ $? -ne 0 ]]; then
   DISTRO=$(head -1 /etc/issue | cut -f 1 -d " " | tr [A-Z] [a-z])
fi

if [[ "$DISTRO" == "" ]]; then
    echo "Can't determine distro"
fi

VIRTUALENVPATH="/tmp/env"

if [[ "$TRAVIS" -eq 1 ]]; then
    VIRTUALENVPATH="$VIRTUAL_ENV"
fi

function test_setup_develop_root(){
test_setup "test/install_files/${install_type}_${pyenv}_${DISTRO}"
}

function test_setup(){
error_found=0
for file in $(awk '{print $2}' $1| sed "s:VIRTUALENVPATH:$VIRTUALENVPATH:g"); do
    exp_chmod=$(grep "$file$" $1| cut -d " " -f 1 )
    cur_chmod=$(stat -c "%A" $file 2>> /tmp/stat.failure)
    if [[ $? -ne 0 ]];then
        tail -1 /tmp/stat.failure
        if [[ $STOP_ON_FAILURE -eq 1 ]];then
            return 1
        else
            error_found=1
        fi
    fi

    if [[ "$exp_chmod" != "$cur_chmod" ]]; then
        echo "Right error on file $file - expected: $exp_chmod, found: $cur_chmod"
        if [[ $STOP_ON_FAILURE -eq 1 ]]; then
            return 1
        else
            error_found=1
        fi
    fi
done 

return $error_found
}

deactivate () {
    unset pydoc

    # reset old environment variables
    if [ -n "$_OLD_VIRTUAL_PATH" ] ; then
        PATH="$_OLD_VIRTUAL_PATH"
        export PATH
        unset _OLD_VIRTUAL_PATH
    fi
    if [ -n "$_OLD_VIRTUAL_PYTHONHOME" ] ; then
        PYTHONHOME="$_OLD_VIRTUAL_PYTHONHOME"
        export PYTHONHOME
        unset _OLD_VIRTUAL_PYTHONHOME
    fi

    # This should detect bash and zsh, which have a hash command that must
    # be called to get it to forget past commands.  Without forgetting
    # past commands the $PATH changes we made may not be respected
    if [ -n "$BASH" -o -n "$ZSH_VERSION" ] ; then
        hash -r 2>/dev/null
    fi

    if [ -n "$_OLD_VIRTUAL_PS1" ] ; then
        PS1="$_OLD_VIRTUAL_PS1"
        export PS1
        unset _OLD_VIRTUAL_PS1
    fi

    unset VIRTUAL_ENV
    if [ ! "$1" = "nondestructive" ] ; then
    # Self destruct!
        unset -f deactivate
    fi
}

#TODO
# go though install files and assert right are correct
# check owner also
# for now all was done in root. Maybe we will need specific user tests

error_found=0
#echo "VIRTUAL:$VIRTUAL_ENV"
#env

#Will copy it from activate
deactivate 
 
for pyenv in "root" "virtualenv"; do
    if [[ "$pyenv" == "virtualenv" ]]; then
        source $VIRTUALENVPATH/bin/activate
        SUDO=""
    else
        SUDO="sudo"
    fi
    for install_type in "install" "develop"; do
        if [[ ! -e ./test/install_files/${install_type}_${pyenv}_${DISTRO} ]]; then
            echo "DISTRO $DISTRO not supported for python setup.py $install_type $pyenv"
            continue
        fi
        $SUDO pip install -r test/requirements.txt # may require sudo
        $SUDO python setup.py $install_type --owner=$(id -u -n) --group=$(id -g -n) # may require sudo
        #test_setup_${install_type}_${pyenv}
        test_setup "test/install_files/${install_type}_${pyenv}_${DISTRO}"

        if [[ $? -ne 0 ]];then
            if [[ $STOP_ON_FAILURE -eq 1 ]];then
                exit 1
            else
                error_found=1
            fi
        fi

        $SUDO pip uninstall -y shinken
        $SUDO ./test/uninstall_shinken.sh $install_type $pyenv
    done
done

exit $error_found
