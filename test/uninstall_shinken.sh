function remove_develop_root(){
    find /usr/ -name "Shinken.egg-link" -exec rm {} \;
    # rm -rf build
    # rm -rf Shinken.egg-info
}

function remove_develop_virtualenv(){
    find ~ -name "Shinken.egg-link" -exec rm {} \;
    # rm -rf build
    # rm -rf Shinken.egg-info
}

function remove_install_virtualenv(){
    find ~ -name "Shinken*.egg" -exec rm -rf {} \;
}

if [[ "$#" -ne 2 ]]; then
    echo "Please specify install method and env [install|develop] [virtualenv|root]"
    echo "Example : $0 develop virtualenv"
fi


