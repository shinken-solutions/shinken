STOP_ON_FAILURE=0

DISTRO=$(lsb_release -i | cut -f 2 | tr [A-Z] [a-z])

if [[ $? -ne 0 ]];then
   DISTRO=$(head -1 /etc/issue | cut -f 1 -d " " | tr [A-Z] [a-z])
fi

if [[ $DISTRO == "" ]]; then
    echo "Can't determine distro"
fi

function test_setup_develop_root(){
test_setup "test/install_files/${install_type}_${pyenv}_${DISTRO}"
}

function test_setup(){
error_found=0
for line in $1; do
    file=$(echo $line | cut -d " " -f 2)
    exp_chmod=$(echo $line | cut -d " " -f 1)
    cur_chmod=$(stat -c "%A" $file 2>> /tmp/stat.failure)
    if [[ $? -ne 0 ]];then
        tail -1 /tmp/stat.failure
        if [[ $STOP_ON_FAILURE -eq 1 ]];then
            return 1
        else
            error_found=1
        fi
    fi

    if [[ "$exp_chmod" != "$cur_chmod" ]]; then
        echo "Right error on file $file - expected: $exp_chmod, found: $cur_chmod"
        if [[ $STOP_ON_FAILURE -eq 1 ]];then
            return 1
        else
            error_found=1
        fi
    fi

    return $error_found

done 
}

#TODO
# go though install files and assert right are correct
# check owner also
# for now all was done in root. Maybe we will need specific user tests

error_found=0
for pyenv in "root" "virtualenv"; do
    for install_type in "install" "develop"; do
        if [[ ! -e ./test/install_files/${install_type}_${pyenv}_${DISTRO} ]]; then
            echo "DISTRO $DISTRO not supported for python setup.py $install_type $pyenv"
        fi
        python setup.py $install_type $pyenv
        #test_setup_${install_type}_${pyenv}
        test_setup "test/install_files/${install_type}_${pyenv}_${DISTRO}"

        if [[ $STOP_ON_FAILURE -eq 1 ]];then
            exit 1
        else
            error_found=1
        fi

        pip uninstall shinken
        ./test/uninstall_shinken.sh $install_type $pyenv
    done
done

exit $error_found
