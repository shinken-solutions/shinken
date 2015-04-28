function remove_develop_root(){
    find /usr/ -name "Shinken.egg-link" -exec rm -f {} \;
    # rm -rf build
    # rm -rf Shinken.egg-info
}

function remove_develop_virtualenv(){
    find ~ -name "Shinken.egg-link" -exec rm -f {} \;
    # rm -rf build
    # rm -rf Shinken.egg-info
}

function remove_install_virtualenv(){
    find ~ -name "Shinken*.egg" -exec rm -rf {} \;
}

function remove_install_root(){
    find /usr/ -name "Shinken*.egg" -exec rm -rf {} \;  # pip uninstall should do it
    rm -rf /usr/bin/shinken* /var/lib/shinken /var/log/shinken/
    rm -rf /run/shinken /etc/shinken /etc/default/shinken /etc/init.d/shinken*

}


if [[ "$#" -ne 2 ]]; then
    echo "Please specify install method and env [install|develop] [virtualenv|root]"
    echo "Example : $0 develop virtualenv"
fi

remove_${1}_${2}
