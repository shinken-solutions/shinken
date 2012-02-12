#!/bin/bash 
#set -x 
#Copyright (C) 2009-2012 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    David GUENAULT, dguenault@monitoring-fr.org
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

if [ -f /tmp/shinken.install.log ]
then
    rm -f /tmp/shinken.install.log    
fi 

#####################
### ENVIRONNEMENT ###
#####################

export myscripts=$(readlink -f $(dirname $0))
src=$(readlink -f "$myscripts/../../..")
. $myscripts/shinken.conf

function trap_handler()
{
        MYSELF="$0"               # equals to my script name
        LASTLINE="$1"            # argument 1: last line of error occurence
        LASTERR="$2"             # argument 2: error code of last command
        FUNCTION="$3"
        if [ -z "$3" ]
        then
                cecho "[FATAL] Unexpected error on line ${LASTLINE}" red
        else
                cecho "[FATAL] Unexpected error on line ${LASTLINE} in function ${FUNCTION} ($LASTERR)" red
        fi
        exit 2
}

function remove(){
    cadre "Removing shinken" green
    skill
    
    if [ -d "$TARGET" ]
    then 
        cecho " > Removing $TARGET" green
        rm -Rf $TARGET
    fi
    if [ -h "/etc/default/shinken" ]
    then 
        cecho " > Removing defaults" green
        rm -Rf /etc/default/shinken 
    fi
    if [ -f "/etc/init.d/shinken" ]
    then
        cecho " > Removing startup scripts" green
        case $CODE in
            REDHAT)
                chkconfig shinken off
                chkconfig --del shinken
                ;;
            DEBIAN)
                update-rc.d -f shinken remove >> /tmp/shinken.install.log 2>&1 
                ;;
            esac    
    fi
    rm -f /etc/init.d/shinken*

    if [ -d "$PNPPREFIX" ]
    then
        doremove="n"
        cread " > found a pnp4nagios installation : do you want to remove it ? (y|N) =>  " yellow "n" "y n" 
        if [ "$readvalue" == "y" ]
        then
            cecho " > Removing pnp4nagios" green
            rm -Rf $PNPPREFIX
            case $CODE in
                    REDHAT)
                            /etc/init.d/npcd stop >> /tmp/shinken.install.log 2>&1
                            chkconfig npcd off >> /tmp/shinken.install.log 2>&1
                            chkconfig --del npcd  >> /tmp/shinken.install.log 2>&1
                            rm -f /etc/init.d/npcd >> /tmp/shinken.install.log 2>&1
                            rm -f /etc/httpd/conf.d/pnp4nagios.conf >> /tmp/shinken.install.log 2>&1
                            /etc/init.d/httpd restart >> /tmp/shinken.install.log 2>&1
                            ;;
                    DEBIAN)
                            /etc/init.d/npcd stop >> /tmp/shinken.install.log 2>&1
                            update-rc.d -f npcd remove >> /tmp/shinken.install.log 2>&1 
                            rm -f /etc/init.d/npcd >> /tmp/shinken.install.log 2>&1
                            rm -f /etc/apache2/conf.d/pnp4nagios.conf >> /tmp/shinken.install.log 2>&1
                            /etc/init.d/apache2 restart >> /tmp/shinken.install.log 2>&1
                            ;;
            esac   
        else 
            cecho " > Aborting uninstallation of pnp4nagios" yellow
        fi
    fi

    if [ -d "$MKPREFIX" ]
    then
        doremove="n"
        cread " > found a check_mk multisite installation : do you want to remove it ? (y|N) =>  " yellow "n" "y n" 
        if [ "$readvalue" == "y" ]
        then
            cecho " > Removing check_mk multisite" green
            rm -Rf $MKPREFIX
            if [ -d $PNPPREFIX.MK ]
            then
                rm -Rf $PNPPREFIX.MK
            fi
            case $CODE in
                    REDHAT)
                            rm -f /etc/httpd/conf.d/zzz_check_mk.conf >> /tmp/shinken.install.log 2>&1
                            /etc/init.d/httpd restart >> /tmp/shinken.install.log 2>&1
                            ;;
                    DEBIAN)
                            rm -f /etc/apache2/conf.d/zzz_check_mk.conf >> /tmp/shinken.install.log 2>&1
                            /etc/init.d/apache2 restart >> /tmp/shinken.install.log 2>&1
                            ;;
            esac   
        else 
            cecho " > Aborting uninstallation of check_mk multisite" yellow
        fi
    fi

    if [ -d "$NAGVISPREFIX" ]
    then
        doremove="n"
        cread " > found a nagvis installation : do you want to remove it ? (y|N) =>  " yellow "n" "y n" 
        if [ "$readvalue" == "y" ]
        then
            cecho " > Removing nagvis" green
            rm -Rf $NAGVISPREFIX
            case $CODE in
                    REDHAT)
                            rm -f /etc/httpd/conf.d/nagvis.conf >> /tmp/shinken.install.log 2>&1
                            /etc/init.d/httpd restart >> /tmp/shinken.install.log 2>&1
                            ;;
                    DEBIAN)
                            rm -f /etc/apache2/conf.d/nagvis.conf >> /tmp/shinken.install.log 2>&1
                            /etc/init.d/apache2 restart >> /tmp/shinken.install.log 2>&1
                            ;;
            esac   
        else 
            cecho " > Aborting uninstallation of nagvis" yellow
        fi
    fi

    return 0
}

function purgeSQLITE(){
    cadre "Purge livestatus db logs" green
    if [ ! -f $TARGET/var/livestatus.db ]
    then
        cecho " > Livestatus db not found " yellow
        exit 1
    fi
    skill >> /tmp/shinken.install.log 2>&1 
    cecho " > We keep $KEEPDAYSLOG days of logs" green
    sqlite3 $TARGET/var/livestatus.db "delete from logs where time < strftime('%s', 'now') - 3600*24*$KEEPDAYSLOG"
    cecho " > Vaccum the sqlite DB" green
    sqlite3 $TARGET/var/livestatus.db VACUUM
}

function skill(){
    /etc/init.d/shinken stop >> /tmp/shinken.install.log 2>&1 
    pc=$(ps -aef | grep "$TARGET" | grep -v "grep" | wc -l )
    if [ $pc -ne 0 ]
    then    
        OLDIFS=$IFS
        IFS=$'\n'
        for p in $(ps -aef | grep "$TARGET" | grep -v "grep" | awk '{print $2}')
        do
            cecho " > Killing $p " green
            kill -9 $p
        done

        IFS=$OLDIFS
    fi
    rm -Rf /tmp/bad_start*
    rm -Rf $TARGET/var/*.pid
}


function setdirectives(){
    trap 'trap_handler ${LINENO} $? setdirectives' ERR
    directives=$1
    fic=$2
    mpath=$3
    
    cecho "    > Going to $mpath" green
    cd $mpath

    for pair in $directives
    do
        directive=$(echo $pair | awk -F= '{print $1}')
        value=$(echo $pair | awk -F= '{print $2}')
        cecho "       > Setting $directive to $value in $fic" green
        sed -i 's#^\# \?'$directive'=\(.*\)$#'$directive'='$value'#g' $mpath/etc/$(basename $fic)
    done
}

##############################
### INSTALLATION FUNCTIONS ###
##############################

function create_user(){
    trap 'trap_handler ${LINENO} $? create_user' ERR
    cadre "Creating user" green
    if [ ! -z "$(cat /etc/passwd | grep $SKUSER)" ] 
    then
        cecho " > User $SKUSER already exists" yellow 
    else
            useradd -s /bin/bash $SKUSER -m -d /home/$SKUSER 
    fi
        usermod -G $SKGROUP $SKUSER 
}

function check_exist(){
    trap 'trap_handler ${LINENO} $? check_exist' ERR
    cadre "Checking for existing installation" green
    if [ -d "$TARGET" ]
    then
        cecho " > Target folder already exists" red
        exit 2
    fi
    if [ -e "/etc/init.d/shinken" ]
    then
        cecho " > Init scripts already exists" red
        exit 2
    fi
    if [ -L "/etc/default/shinken" ]
    then
        cecho " > Shinken default already exists" red
        exit 2
    fi

}

function installpkg(){
    type=$1
    package=$2

    if [ "$type" == "python" ]
    then
        easy_install $package >> /tmp/shinken.install.log 2>&1 
        return $?
    fi

    case $CODE in 
        REDHAT)
            yum install -yq $package >> /tmp/shinken.install.log 2>&1 
            if [ $? -ne 0 ]
            then
                return 2
            fi
            ;;
        DEBIAN)
            apt-get install -y $package  >> /tmp/shinken.install.log 2>&1 
            if [ $? -ne 0 ]
            then
                return 2
            fi
            ;;
    esac    
    return 0
}

function debinstalled(){
    package=$1
    if [ -z "$(dpkg -l $package | grep "^ii")" ]
    then
        return 1
    else
        return 0
    fi
}

function prerequisites(){
    cadre "Checking prerequisites" green
    # common prereq
    bins="wget sed awk grep python bash"

    for b in $bins
    do
        rb=$(which $b)
        if [ $? -eq 0 ]
        then
            cecho " > Checking for $b : OK" green 
        else
            cecho " > Checking for $b : NOT FOUND" red
            exit 2 
        fi    
    done

    # distro prereq
    case $CODE in
        REDHAT)
            case $VERS in
                [5-6])
                    PACKAGES=$YUMPKGS
                    QUERY="rpm -q "
                    cd $TMP
                    $QUERY $EPELNAME >> /tmp/shinken.install.log 2>&1 
                    if [ $? -ne 0 ]
                    then
                        cecho " > Installing $EPELPKG" yellow
                        wget $WGETPROXY $EPEL  >> /tmp/shinken.install.log 2>&1  
                        if [ $? -ne 0 ]
                        then
                            cecho " > Error while trying to download EPEL repositories" red 
                            exit 2
                        fi
                        rpm -Uvh ./$EPELPKG >> /tmp/shinken.install.log 2>&1 
                    else
                        cecho " > $EPELPKG already installed" green 
                    fi
                    ;;
#                6)
#                    PACKAGES=$YUMPKGS
#                    QUERY="rpm -q "
#                    ;;
                *)
                    cecho " > Unsupported RedHat/CentOs version" red
                    exit 2
                    ;;
            esac
            ;;

        DEBIAN)
            PACKAGES=$APTPKGS
            QUERY="debinstalled "
            ;;
    esac
    for p in $PACKAGES
    do
        $QUERY $p >> /tmp/shinken.install.log 2>&1 
        if [ $? -ne 0 ]
        then
            cecho " > Installing $p " yellow
            installpkg pkg $p 
            if [ $? -ne 0 ]
            then 
                cecho " > Error while trying to install $p" red 
                exit 2     
            fi
        else
            cecho " > Package $p already installed " green 
        fi
    done
    # python prereq
    if [ "$CODE" = "REDHAT" ]
    then
        case $VERS in
            5)
                # install setup tools for python 26
                export PY="python26"
                export PYEI="easy_install-2.6"
                if [ ! -d "setuptools-$SETUPTOOLSVERS" ]
                then
                    cecho " > Downloading setuptools for python 2.6" green
                    wget $WGETPROXY $RHELSETUPTOOLS >> /tmp/shinken.install.log 2>&1 
                    tar zxvf setuptools-$SETUPTOOLSVERS.tar.gz >> /tmp/shinken.install.log 2>&1 
                fi
                cecho " > Installing setuptools for python 2.6" green
                cd setuptools-$SETUPTOOLSVERS >> /tmp/shinken.install.log 2>&1 
                python26 setup.py install >> /tmp/shinken.install.log 2>&1 
                PYLIBS=$PYLIBSRHEL
                ;;
            6)
                export PY="python"
                export PYEI="easy_install"
                PYLIBS=$PYLIBSRHEL6
                ;;
        esac
        for p in $PYLIBS
        do
            module=$(echo $p | awk -F: '{print $1'})
            import=$(echo $p | awk -F: '{print $2'})

            $PY $myscripts/tools/checkmodule.py -m $import  >> /tmp/shinken.install.log 2>&1 
            if [ $? -eq 2 ]
            then
                cecho " > Module $module ($import) not found. Installing..." yellow
                $PYEI $module >> /tmp/shinken.install.log 2>&1 
            else
                cecho " > Module $module found." green 
            fi

            
        done
    elif [ "$CODE" == "DEBIAN" ]
    then    
        export PY="python"
        export PYEI="easy_install"
        PYLIBS=$PYLIBSDEB
        for p in $PYLIBS
        do
            module=$(echo $p | awk -F: '{print $1'})
            import=$(echo $p | awk -F: '{print $2'})

            $PY $myscripts/tools/checkmodule.py -m $import  >> /tmp/shinken.install.log 2>&1 
            if [ $? -eq 2 ]
            then
                cecho " > Module $module ($import) not found. Installing..." yellow
                $PYEI $module >> /tmp/shinken.install.log 2>&1 
            else
                cecho " > Module $module found." green 
            fi

            
        done
    fi
    
}

function check_distro(){
    trap 'trap_handler ${LINENO} $? check_distro' ERR
    cadre "Verifying compatible distros" green

    if [ ! -e /usr/bin/lsb_release ]
    then    
        cecho " > No compatible distribution found" red
        cecho " > maybe the lsb_release utility is not found" red
        cecho " > on redhat like distro you should try yum install redhat-lsb"
        exit 2
    fi

    if [ -z "$CODE" ]
    then
        cecho " > $DIST is not supported" red
        exit 2
    fi

    versionok=0
    distrook=0

    for d in $DISTROS
    do
        distro=$(echo $d | awk -F: '{print $1}')
        version=$(echo $d | awk -F: '{print $2}')
        if [ "$CODE" = "$distro" ]
        then
            cecho " > Found $CODE" green
            if [ "$version" = "" ]
            then
                cecho " > Version checking for $DIST is not needed" green
                versionok=1
                return
            else
                if [ "$VERS" = "$version" ]
                then
                    versionok=1
                    return
                #else
                #    versionok=0
                fi        
            fi
        fi
    done

    if [ $versionok -ne 1 ]
    then    
        cecho " > $DIST $VERS is not supported" red
        exit 2
    fi

    cecho " > Found $DIST $VERS" yellow 
}

function get_from_git(){
    trap 'trap_handler ${LINENO} $? get_from_git' ERR
    cadre "Getting shinken" green
    cd $TMP
    if [ -e "shinken" ]
    then
        rm -Rf shinken
    fi
    env GIT_SSL_NO_VERIFY=true git clone $GIT >> /tmp/shinken.install.log 2>&1 
    cd shinken
    cecho " > Switching to version $VERSION" green
    git checkout $VERSION >> /tmp/shinken.install.log 2>&1 
    export src=$TMP/shinken
    # clean up .git folder
    rm -Rf .git
}

function relocate(){
    trap 'trap_handler ${LINENO} $? relocate' ERR
    cadre "Relocate source tree to $TARGET" green
    # relocate source tree
    cd $TARGET
    
    # relocate macros
    for f in $(find $TARGET/contrib/alternative-installation/shinken-install/tools/macros | grep "\.macro$")
    do
        cecho " > relocating macro $f" green
        sed -i "s#__PREFIX__#$TARGET#g" $f
    done

    # relocate nagios plugin path
    sed -i "s#/usr/lib/nagios/plugins#$TARGET/libexec#g" ./etc/resource.cfg
    sed -i "s#/usr/local/shinken/libexec#$TARGET/libexec#g" ./etc/resource.cfg
    # relocate default /usr/local/shinken path
    for fic in $(find . | grep -v "shinken-install" | grep -v "\.pyc$" | xargs grep -snH "/usr/local/shinken" --color | cut -f1 -d' ' | awk -F : '{print $1}' | sort | uniq)
    do 
        cecho " > Processing $fic" green
        cp "$fic" "$fic.orig" 
        #sed -i 's#/opt/shinken#'$TARGET'#g' $fic 
        sed -i 's#/usr/local/shinken#'$TARGET'#g' "$fic"
    done

    # when read hat 5 try to use python26
    if [ "$CODE" = "REDHAT" ]
    then
        if [ "$VERS" = "5" ]
        then
            cecho " > Translating python version to python26" green
            for fic in $(find $TARGET | grep "\.py$") 
            do
                sed -i "s#/usr/bin/env python#/usr/bin/python26#g" $fic
            done
            # also try to translate python script without py extension
            for fic in $(find $TARGET/bin)
            do
                if [ ! -z "$(file $fic | grep "python")" ]
                then
                    sed -i "s#/usr/bin/env python#/usr/bin/python26#g" $fic
                fi
            done
        fi
    fi

    # set some directives 
    cadre "Set some configuration directives" green
    directives="workdir=$TARGET/var user=$SKUSER group=$SKGROUP"
    for fic in $(ls -1 etc/*.ini)
    do 
        cecho " > Processing $fic" green;
        setdirectives "$directives" $fic $TARGET
        #cp -f $fic $TARGET/etc/; 
    done
    # relocate default file
    cd $TARGET/bin/default
    cat $TARGET/bin/default/shinken.in | sed  -e 's#LOG\=\(.*\)$#LOG='$TARGET'/var#g' -e 's#RUN\=\(.*\)$#RUN='$TARGET'/var#g' -e  's#ETC\=\(.*\)$#ETC='$TARGET'/etc#g' -e  's#VAR\=\(.*\)$#VAR='$TARGET'/var#g' -e  's#BIN\=\(.*\)$#BIN='$TARGET'/bin#g' > $TARGET/bin/default/shinken
    # relocate init file
    cd $TARGET/bin/init.d
    mv shinken shinken.in
    cat shinken.in | sed -e "s#\#export PYTHONPATH=.*#export PYTHONPATH="$TARGET"#g" > $TARGET/bin/init.d/shinken
}

function fix(){
    trap 'trap_handler ${LINENO} $? fix' ERR
    cadre "Applying various fixes" green
    chmod +x /etc/init.d/shinken
    chmod +x /etc/default/shinken
    chmod +x $TARGET/bin/init.d/shinken
    chown -R $SKUSER:$SKGROUP $TARGET
    chmod -R g+w $TARGET
    # remove tests directory
    rm -Rf $TARGET/test
}

function enable(){
    trap 'trap_handler ${LINENO} $? enable' ERR
    cadre "Enabling startup scripts" green
    cp $TARGET/bin/init.d/shinken* /etc/init.d/
    case $DISTRO in
        REDHAT)
            cecho " > Enabling $DIST startup script" green
            chkconfig --add shinken
            chkconfig shinken on
            ;;
        DEBIAN)
            cecho " > Enabling $DIST startup script" green
            update-rc.d shinken defaults >> /tmp/shinken.install.log 2>&1 
            ;;
    esac    
}

function sinstall(){
    #trap 'trap_handler ${LINENO} $? install' ERR
    #cecho "Installing shinken" green
    check_distro
    check_exist
    prerequisites
    create_user
    cp -Rf $src $TARGET
    relocate
    ln -s $TARGET/bin/default/shinken /etc/default/shinken
    cp $TARGET/bin/init.d/shinken* /etc/init.d/
    mkdir -p $TARGET/var/archives
    enableretention
    if [ "$LOGSTORE" == "mongo" ]
    then
        enablemongologs 
    fi
    fix
    cecho "+------------------------------------------------------------------------------" green
    cecho "| Shinken is now installed on your server " green
    cecho "| You can start it with /etc/init.d/shinken start " green
    cecho "| The Web Interface is available at : http://localhost:7767" green
    cecho "+------------------------------------------------------------------------------" green
}


########################
### BACKUP FUNCTIONS ###
########################

function backup(){
    trap 'trap_handler ${LINENO} $? backup' ERR
    cadre "Backup shinken configuration, plugins and data" green
    skill
    if [ ! -e $BACKUPDIR ]
    then
        mkdir $BACKUPDIR
    fi
    mkdir -p $BACKUPDIR/bck-shinken.$DATE
    # Sugg :
    # Add : cp -Rfp $TARGET/bin $BACKUPDIR/bck-shinken.$DATE/ line to backup bin
    cp -Rfp $TARGET/etc $BACKUPDIR/bck-shinken.$DATE/
    cp -Rfp $TARGET/libexec $BACKUPDIR/bck-shinken.$DATE/
    cp -Rfp $TARGET/var $BACKUPDIR/bck-shinken.$DATE/
    cecho " > Backup done. Id is $DATE"
}

function backuplist(){
    trap 'trap_handler ${LINENO} $? backuplist' ERR
    cadre "List of available backups in $BACKUPDIR" green
    for d in $(ls -1 $BACKUPDIR | grep "bck-shinken" | awk -F. '{print $2}')
    do
        cecho " > $d" green
    done

}

function restore(){
    trap 'trap_handler ${LINENO} $? restore' ERR
    cadre "Restore shinken configuration, plugins and data" green
    skill
    if [ ! -e $BACKUPDIR ]
    then
        cecho " > Backup folder not found" red
        exit 2
    fi
    if [ -z $1 ]
    then
        cecho " > No backup timestamp specified" red
        backuplist
        exit 2
    fi
    if [ ! -e $BACKUPDIR/bck-shinken.$1 ]
    then
        cecho " > Backup not found : $BACKUPDIR/bck-shinken.$1 " red
        backuplist
        exit 2
    fi
    rm -Rf $TARGET/etc
    rm -Rf $TARGET/libexec 
    rm -Rf $TARGET/var 
    cp -Rfp $BACKUPDIR/bck-shinken.$1/* $TARGET/
    cecho " > Restoration done" green
}

########################
### UPDATE FUNCTIONS ###
########################

function supdate(){
    trap 'trap_handler ${LINENO} $? update' ERR

    curpath=$(pwd)
    if [ "$src" == "$TARGET" ]
    then
        cecho "You should use the source tree to update and not use the target folder !!!!!" red
        exit 2
    fi

    cadre "Updating shinken" green
    
    skill
    backup
    remove
    get_from_git
    cp -Rf $src $TARGET
    relocate
    ln -sf $TARGET/bin/default/shinken /etc/default/shinken
    cp $TARGET/bin/init.d/shinken* /etc/init.d/
    mkdir -p $TARGET/var/archives
    fix
    restore $DATE
}

##############################
### EXPLOITATION FUNCTIONS ###
##############################

function compresslogs(){
    trap 'trap_handler ${LINENO} $? compresslogs' ERR
    cadre "Compress rotated logs" green
    if [ ! -d $TARGET/var/archives ]
    then
        cecho " > Archives directory not found" yellow
        exit 0
    fi
    cd $TARGET/var/archives
    for l in $(ls -1 ./*.log)
    do
        file=$(basename $l)
        if [ -e $file ]
        then
            cecho " > Processing $file" green
            tar czf $file.tar.gz $file
            rm -f $file
        fi
    done
}

function shelp(){
    cat $myscripts/README
}

########################
### CONFIG FUNCTIONS ###
########################

function cleanconf(){
    if [ -z "$myscripts" ]
    then
        cecho " > Files/Folders list not found" yellow
        exit 2
    else
        for f in $(cat $myscripts/config.files)
        do
            cecho " > Removing $TARGET/etc/$f" green
            rm -Rf $TARGET/etc/$f
        done
    fi
}

function fixsudoers(){
    cecho " > Fix /etc/sudoers file for shinken integration" green
    cp /etc/sudoers /etc/sudoers.$(date +%Y%m%d%H%M%S)
    cat $myscripts/sudoers.centreon | sed -e 's#TARGET#'$TARGET'#g' >> /etc/sudoers
}

function fixcentreondb(){
    cecho " > Fix centreon database path for shinken integration" green

    # get existing db access
    host=$(cat /etc/centreon/conf.pm | grep "mysql_host" | awk '{print $3}' | sed -e "s/\"//g" -e "s/;//g")
    user=$(cat /etc/centreon/conf.pm | grep "mysql_user" | awk '{print $3}' | sed -e "s/\"//g" -e "s/;//g")
    pass=$(cat /etc/centreon/conf.pm | grep "mysql_passwd" | awk '{print $3}' | sed -e "s/\"//g" -e "s/;//g")
    db=$(cat /etc/centreon/conf.pm | grep "mysql_database_oreon" | awk '{print $3}' | sed -e "s/\"//g" -e "s/;//g")

    cp $myscripts/centreon.sql /tmp/centreon.sql
    sed -i 's#TARGET#'$TARGET'#g' /tmp/centreon.sql
    sed -i 's#CENTREON#'$db'#g' /tmp/centreon.sql

    if [ -z "$pass" ]
    then
        mysql -h $host -u $user $db < /tmp/centreon.sql
    else
        mysql -h $host -u $user -p$pass $db < /tmp/centreon.sql
    fi
}

function fixforfan(){
    if [ ! -z "cat /etc/issue | grep FAN" ]
    then
        chown -R apache:nagios $TARGET/etc
        chmod -R g+rw $TARGET/etc/*
    fi
}

# ENABLE MONGO STORAGE FOR LOGS
function enablemongologs(){
    cecho " > Enable mongodb log storage" green
    export PYTHONPATH=$TARGET
    export PY="$(pythonver)"
    result=$($PY $TARGET/contrib/alternative-installation/shinken-install/tools/skonf.py -a macros -f $TARGET/contrib/alternative-installation/shinken-install/tools/macros/enable_log_mongo.macro -d $MONGOSERVER)    
    if [ $? -ne 0 ]
    then
        cecho " > There was an error while trying to enable mongo log storage ($result)" red
        exit 2
    fi
}

function enablendodb(){
    cecho " > FIX shinken ndo configuration" green
    # get existing db access
    host=$(cat /etc/centreon/conf.pm | grep "mysql_host" | awk '{print $3}' | sed -e "s/\"//g" -e "s/;//g")
    user=$(cat /etc/centreon/conf.pm | grep "mysql_user" | awk '{print $3}' | sed -e "s/\"//g" -e "s/;//g")
    pass=$(cat /etc/centreon/conf.pm | grep "mysql_passwd" | awk '{print $3}' | sed -e "s/\"//g" -e "s/;//g")
    db="centreon_status"
    # add ndo module to broker
    # first get existing broker modules
    export PYTHONPATH=$TARGET
    export PY="$(pythonver)"
    result=$($PY $TARGET/contrib/alternative-installation/shinken-install/tools/skonf.py -a macros -f $TARGET/contrib/alternative-installation/shinken-install/tools/macros/ces_enable_ndo.macro -d $host,$db,$user,$pass)
    if [ $? -ne 0 ]
    then
        cecho $result red
        exit 2
    fi
}

function enableretention(){

    cecho " > Enable retention for broker scheduler and arbiter" green

    if [ "$RETENTIONMODULE" == "mongo" ]
    then
        export PYTHONPATH=$TARGET
        export PY="$(pythonver)"

        result=$($PY $TARGET/contrib/alternative-installation/shinken-install/tools/skonf.py -a macros -f $TARGET/contrib/alternative-installation/shinken-install/tools/macros/enable_retention_mongo.macro)    
        if [ $? -ne 0 ]
        then
            cecho $result red
            exit 2
        fi
    else
        export PYTHONPATH=$TARGET
        export PY="$(pythonver)"
        result=$($PY $TARGET/contrib/alternative-installation/shinken-install/tools/skonf.py -a macros -f $TARGET/contrib/alternative-installation/shinken-install/tools/macros/enable_retention.macro)    
        if [ $? -ne 0 ]
        then
            cecho $result red
            exit 2
        fi
    fi
}

function enableperfdata(){

    cecho " > Enable perfdata " green

    export PYTHONPATH=$TARGET
    export PY="$(pythonver)"
    cecho " > Getting existing broker modules list" green
    modules=$($PY $TARGET/contrib/alternative-installation/shinken-install/tools/skonf.py -a getdirective -f $TARGET/etc/shinken-specific.cfg -o broker -d modules)    
    if [ -z "$modules" ]
    then    
        modules="Service-Perfdata, Host-Perfdata"
    else
        modules=$modules", Service-Perfdata, Host-Perfdata"
    fi
    result=$($PY $TARGET/contrib/alternative-installation/shinken-install/tools/skonf.py -q -a setparam -f $TARGET/etc/shinken-specific.cfg -o broker -d modules -v "$modules")
    cecho " > $result" green
}

function setdaemonsaddresses(){
    export PYTHONPATH=$TARGET
    export PY="$(pythonver)"
    localip=$(ifconfig $IF | grep "^ *inet adr:" | awk -F : '{print $2}' | awk '{print $1}')
    result=$($PY $TARGET/contrib/alternative-installation/shinken-install/tools/skonf.py -q -a setparam -f $TARGET/etc/shinken-specific.cfg -o arbiter -d address -v "$localip")
    cecho " > $result" green    
    result=$($PY $TARGET/contrib/alternative-installation/shinken-install/tools/skonf.py -q -a setparam -f $TARGET/etc/shinken-specific.cfg -o scheduler -d address -v "$localip")
    cecho " > $result" green    
    result=$($PY $TARGET/contrib/alternative-installation/shinken-install/tools/skonf.py -q -a setparam -f $TARGET/etc/shinken-specific.cfg -o reactionner -d address -v "$localip")
    cecho " > $result" green    
    result=$($PY $TARGET/contrib/alternative-installation/shinken-install/tools/skonf.py -q -a setparam -f $TARGET/etc/shinken-specific.cfg -o receiver -d address -v "$localip")
    cecho " > $result" green    
    result=$($PY $TARGET/contrib/alternative-installation/shinken-install/tools/skonf.py -q -a setparam -f $TARGET/etc/shinken-specific.cfg -o poller -d address -v "$localip" -r "poller_name=poller-1")
    cecho " > $result" green    
}

function enableCESCentralDaemons(){
    setdaemons "arbiter reactionner receiver scheduler broker poller"  
}

function enableCESPollerDaemons(){
    setdaemons "poller"  
}

function disablenagios(){
    chkconfig nagios off
    chkconfig ndo2db off
    /etc/init.d/nagios stop >> /tmp/shinken.install.log 2>&1 
    /etc/init.d/ndo2db stop >> /tmp/shinken.install.log 2>&1 
}

function setdaemons(){
    daemons="$(echo $1)"
    avail="AVAIL_MODULES=\"$daemons\""
    cecho " > Enabling the followings daemons : $daemons" green
    sed -i "s/^AVAIL_MODULES=.*$/$avail/g" /etc/init.d/shinken
}

function fixHtpasswdPath(){
    export PYTHONPATH=$TARGET
    export PY="$(pythonver)"
    # fix the htpasswd.users file path for WEBUI authentication
    result=$($PY $TARGET/contrib/alternative-installation/shinken-install/tools/skonf.py -f $TARGET/etc/shinken-specific.cfg -a setparam -o module -r "module_name=Apache_passwd" -d "passwd" -v "$TARGET/etc/htpasswd.users")
    cecho " > $result" green    
}


# addons installation

# nagvis

function install_nagvis(){

    cadre "Install pnp4nagios addon" green
    case $CODE in
        REDHAT)
            cecho " > Unsupported" red
            exit 2
            ;;
        DEBIAN)
            cecho " > Installing prerequisites" green
            DEBIAN_FRONTEND=noninteractive apt-get install -y $NAGVISAPTPKGS >> /tmp/shinken.install.log 2>&1
            HTTPDUSER="www-data"
            HTTPDGROUP="www-data"
            HTTPDCONF="/etc/apache2/conf.d"
            ;;
        *)
            cecho " > Unknown distribution : $DIST" red
            exit 2
            ;;
    esac
            
    
    filename=$(echo $NAGVIS | awk -F"/" '{print $NF}')
    folder=$(echo $filename | sed -e "s/\.tar\.gz//g")

    cd /tmp

    if [ -d /tmp/$folder ]
    then 
        rm -Rf $folder
    fi

    if [ ! -f /tmp/$filename ]
    then
        cecho " > Download $filename" green
        wget $WGETPROXY $NAGVIS >> /tmp/shinken.install.log 2>&1
        if [ $? -ne 0 ]
        then
            cecho " > Error while downloading $NAGVIS" red
            exit 2
        fi
    fi
    cecho " > Extract archive content" green
    tar zxvf $filename >> /tmp/shinken.install.log 2>&1
    cd $folder
    cecho " > Install nagvis" green
    ./install.sh -a y -q -F -l "tcp:localhost:50000" -i mklivestatus -n $TARGET -p $NAGVISPREFIX -u $HTTPDUSER -g $HTTPDGROUP -w $HTTPDCONF 
    if [ -d $MKPREFIX ]
    then
        cread " > Found a check_mk multisite installation. Do you want to modify the nagvis url so links redirect to multisite ?" yellow "y" "y n"
        if [ "$readvalue" == "y" ]
        then
            cecho " > Patching links for multisite use" green
            cd $NAGVISPREFIX/etc
            patch < $myscripts/nagvis.multisite.uri.patch
        fi
    fi  
}

# mk multisite

function install_multisite(){
    if [ "$CODE" == "REDHAT" ]
    then
        cecho " > Unsupported" red
        exit 2
    fi
    cadre "Install check_mk addon" green
    cecho " > Configure response file" green
    cp check_mk_setup.conf.in $HOME/.check_mk_setup.conf
    sed -i "s#__PNPPREFIX__#$PNPPREFIX#g" $HOME/.check_mk_setup.conf
    sed -i "s#__MKPREFIX__#$MKPREFIX#g" $HOME/.check_mk_setup.conf
    sed -i "s#__SKPREFIX__#$TARGET#g" $HOME/.check_mk_setup.conf
    sed -i "s#__SKUSER__#$SKUSER#g" $HOME/.check_mk_setup.conf
    sed -i "s#__SKGROUP__#$SKGROUP#g" $HOME/.check_mk_setup.conf
    sed -i "s#__HTTPUSER__#www-data#g" $HOME/.check_mk_setup.conf
    sed -i "s#__HTTPGROUP__#www-data#g" $HOME/.check_mk_setup.conf
    sed -i "s#__HTTPD__#/etc/apache2#g" $HOME/.check_mk_setup.conf
    sed -i "s#__HTTPD__#/etc/apache2#g" $HOME/.check_mk_setup.conf
    cd /tmp
    cecho " > Installing prerequisites" green
    for p in $MKAPTPKG
    do
        cecho " -> Installing $p" green
        apt-get --force-yes -y install $p >> /tmp/shinken.install.log 2>&1 
    done

    filename=$(echo $MKURI | awk -F"/" '{print $NF}')
    folder=$(echo $filename | sed -e "s/\.tar\.gz//g")
    if [ ! -f "$filename" ]
    then 
        cecho " > Getting check_mk archive" green
        wget $WGETPROXY $MKURI >> /tmp/shinken.install.log 2>&1 
    fi
    
    cecho " > Extracting archive" green
    if [ -d "$folder" ]
    then 
        rm -Rf $folder
    fi 
    tar zxvf $filename >> /tmp/shinken.install.log 2>&1 
    cd $folder

    # check if pnp4nagios is here if not move the resulting folder 
    movepnp=0
    if [ ! -d "$PNPPREFIX" ]
    then
        movepnp=1
    fi

    cecho " > Install multisite" green
    ./setup.sh --yes >> /tmp/shinken.install.log 2>&1 
    cecho " > Default configuration for multisite" green
    echo 'sites = {' >> $MKPREFIX/etc/multisite.mk
    echo '   "default": {' >> $MKPREFIX/etc/multisite.mk
    echo '    "alias":          "default",' >> $MKPREFIX/etc/multisite.mk
    echo '    "socket":         "tcp:127.0.0.1:50000",' >> $MKPREFIX/etc/multisite.mk
    echo '    "url_prefix":     "/",' >> $MKPREFIX/etc/multisite.mk
    echo '   },' >> $MKPREFIX/etc/multisite.mk
    echo ' }' >> $MKPREFIX/etc/multisite.mk
    rm -Rf $TARGET/etc/check_mk.d/*
    cecho " > Fix www-data group" green
    usermod -a -G $SKGROUP www-data 
    chown -R $SKUSER:$SKGROUP $TARGET/etc/check_mk.d
    chmod -R g+rwx $TARGET/etc/check_mk.d
    chown -R $SKUSER:$SKGROUP $MKPREFIX/etc/conf.d
    chmod -R g+rwx $MKPREFIX/etc/conf.d
    service apache2 restart >> /tmp/shinken.install.log 2>&1 
    cecho " > Enable sudoers commands for check_mk" green
    echo "# Needed for WATO - the Check_MK Web Administration Tool" >> /etc/sudoers
    echo "Defaults:www-data !requiretty" >> /etc/sudoers
    echo "www-data ALL = (root) NOPASSWD: $MKTARGET/check_mk --automation *" >> /etc/sudoers
    if [ $movepnp -eq 1 ]
    then 
        mv $PNPPREFIX $PNPPREFIX.MK
    fi
}

# pnp4nagios
function install_pnp4nagios(){
    cadre "Install pnp4nagios addon" green
    if [ "$CODE" == "REDHAT" ]
    then
        cecho " > Installing prerequisites" green
        yum -yq install $PNPYUMPKG >> /tmp/shinken.install.log 2>&1
    else
        cecho " > Installing prerequisites" green
        apt-get -y install $PNPAPTPKG >> /tmp/shinken.install.log 2>&1
    fi
    cd /tmp

    filename=$(echo $PNPURI | awk -F"/" '{print $NF}')
    folder=$(echo $filename | sed -e "s/\.tar\.gz//g")
    if [ ! -f "$filename" ]
    then 
        cecho " > Getting pnp4nagios archive" green
        wget $WGETPROXY $PNPURI >> /tmp/shinken.install.log 2>&1 
    fi
    
    cecho " > Extracting archive" green
    if [ -d "$folder" ]
    then 
        rm -Rf $folder
    fi 
    tar zxvf $filename >> /tmp/shinken.install.log 2>&1 
    cd $folder
    #cecho " > Enable mod rewrite for apache" green 
    #a2enmod rewrite >> /tmp/shinken.install.log 2>&1
    if [ "$CODE" == "REDHAT" ]
    then
        /etc/init.d/httpd restart >> /tmp/shinken.install.log 2>&1
    else
        /etc/init.d/apache2 restart >> /tmp/shinken.install.log 2>&1 
    fi
    cecho " > Configuring source tree" green
    ./configure --prefix=$PNPPREFIX --with-nagios-user=$SKUSER --with-nagios-group=$SKGROUP >> /tmp/shinken.install.log 2>&1     
    cecho " > Building ...." green
    make all >> /tmp/shinken.install.log 2>&1 
    cecho " > Installing" green
    make fullinstall >> /tmp/shinken.install.log 2>&1 
    rm -f $PNPPREFIX/share/install.php
    if [ "$CODE" == "REDHAT" ]
    then
        cecho " > Fix htpasswd.users path" green
        sed -i "s#/usr/local/nagios/etc/htpasswd.users#$TARGET/etc/htpasswd.users#g" /etc/httpd/conf.d/pnp4nagios.conf 
        /etc/init.d/apache2 restart >> /tmp/shinken.install.log 2>&1 
    else
        cecho " > Fix htpasswd.users path" green
        sed -i "s#/usr/local/nagios/etc/htpasswd.users#$TARGET/etc/htpasswd.users#g" /etc/apache2/conf.d/pnp4nagios.conf 
        /etc/init.d/apache2 restart >> /tmp/shinken.install.log 2>&1 
    fi
    cecho " > Enable npcdmod" green
    ip=$(ifconfig | grep "inet adr" | grep -v 127.0.0.1 | awk '{print $2}' | awk -F : '{print $2}' | head -n 1)
    do_skmacro enable_npcd.macro $PNPPREFIX/etc/npcd.cfg,$ip 
}


function do_skmacro(){
    macro=$1
    args=$2
    export PYTHONPATH="$TARGET"
    export SHINKEN="$PYTHONPATH"
    export SKTOOLS="$PYTHONPATH/contrib/alternative-installation/shinken-install/tools"
    $PY $SKTOOLS/skonf.py -a macros -f $SKTOOLS/macros/$macro -d $args >> /tmp/shinken.install.log 2>&1 
}


#################################
### PLUGINS INSTALLATION PART ###
#################################

# CAPTURE_PLUGIN
function install_capture_plugin(){
    cadre "Install capture_plugin" green
    cd /tmp
    cecho " > Getting capture_plugin" green
    wget $WGETPROXY http://www.waggy.at/nagios/capture_plugin.txt >> /tmp/shinken.install.log 2>&1 
    cecho " > Installing capture_plugin" green
    mv capture_plugin.txt $TARGET/libexec/capture_plugin
    chmod +x $TARGET/libexec/capture_plugin    
    chown $SKUSER:$SKGROUP $TARGET/libexec/capture_plugin
}

# CHECK_HPASM
function install_check_hpasm(){

    cadre "Install check_hpasm plugin from consol.de" green
    cecho "You must install hpasm and or hp snmp agents on the monitored servers" yellow
    read taste

    if [ "$CODE" == "REDHAT" ]
    then
        cecho " > Installing prerequisites" green 
        yum install -yq $CHECKHPASMYUMPKGS  >> /tmp/shinken.install.log 2>&1 
    else
        cecho " > Installing prerequisites" green 
        apt-get -y install $CHECKHPASMAPTPKGS >> /tmp/shinken.install.log 2>&1 
    fi

    if [ $? -ne 0 ]
    then
        cecho " > Error while installing prerequisites" red
        exit 2
    fi

    cd /tmp

    archive=$(echo $CHECKHPASM | awk -F/ '{print $NF}')
    folder=$(echo $archive | sed -e 's/\.tar\.gz//g')

    if [ ! -f "/tmp/$archive" ]
    then
        cecho " > Downloading check_hpasm" green
        wget $WGETPROXY $CHECKHPASM  >> /tmp/shinken.install.log 2>&1     
        if [ $? -ne 0 ]
        then
            cecho " > Error while downloading check_hpasm" red
            exit 2
        fi
    fi
    cecho " > Extract archive content" green
    tar zxvf $archive >> /tmp/shinken.install.log 2>&1
    cd $folder
    cecho " > Configure source tree" green
    ./configure >> /tmp/shinken.install.log 2>&1
    if [ $? -ne 0 ]
    then
        cecho " > Error while configuring source tree" red
        exit 2
    fi
    cecho " > Build" green
    make  >> /tmp/shinken.install.log 2>&1
    if [ $? -ne 0 ]
    then
        cecho " > Error while building" red
        exit 2
    fi
    cecho " > Installing check_hpasm" green
    cp plugins-scripts/check_hpasm $TARGET/libexec/ >> /tmp/shinken.install.log 2>&1
    chmod +x $TARGET/libexec/check_hpasm  >> /tmp/shinken.install.log 2>&1   
    chown $SKUSER:$SKGROUP $TARGET/libexec/check_hpasm >> /tmp/shinken.install.log 2>&1
}

# CHECK_MONGODB
function install_check_mongodb(){

    cadre "Install check_mongodb plugin from Mike Zupan" green

    if [ "$CODE" == "REDHAT" ]
    then
        cecho " > Installing prerequisites" green 
        yum install -yq $CHECKMONGOYUMPKG  >> /tmp/shinken.install.log 2>&1 
    else
        cecho " > Installing prerequisites" green 
        apt-get -y install $CHECKMONGOAPTPKG >> /tmp/shinken.install.log 2>&1 
    fi

    if [ $? -ne 0 ]
    then
        cecho " > Error while installing prerequisites" red
        exit 2
    fi

    cd /tmp

    if [ ! -f "/tmp/check_mongodb.py" ]
    then
        cecho " > Downloading check_mongodb.py" green
        wget $WGETPROXY $CHECKMONGO  >> /tmp/shinken.install.log 2>&1     
        if [ $? -ne 0 ]
        then
            cecho " > Error while downloading check_mongodb.py" red
            exit 2
        fi
    fi

    cecho " > Installing check_mongodb.py" green
    mv check_mongodb.py $TARGET/libexec/check_mongodb.py
    chmod +x $TARGET/libexec/check_mongodb.py    
    chown $SKUSER:$SKGROUP $TARGET/libexec/check_mongodb.py
        
}

# CHECK_NWC_HEALTH
function install_check_nwc_health(){

    cadre "Install check_nwc_health plugin" green

    if [ "$CODE" == "REDHAT" ]
    then
        if [ ! -z "$CHECKNWCYUMPKG" ]
        then 
            cecho " > Installing prerequisites" green 
            yum install -yq $CHECKNWCYUMPKG  >> /tmp/shinken.install.log 2>&1 
        fi
    else
        if [ ! -z "$CHECKNWCAPTPKG" ]
        then 
            cecho " > Installing prerequisites" green 
            apt-get -y install $CHECKNWCAPTPKG >> /tmp/shinken.install.log 2>&1 
        fi
    fi

    if [ $? -ne 0 ]
    then
        cecho " > Error while installing prerequisites" red
        exit 2
    fi

    cd /tmp

    if [ ! -f "/tmp/master" ]
    then
        cecho " > Downloading check_nwc_health" green
        wget $WGETPROXY $CHECKNWC -O check_nwc_health.tar.gz  >> /tmp/shinken.install.log 2>&1     
        if [ $? -ne 0 ]
        then
            cecho " > Error while downloading check_wc" red
            exit 2
        fi
    fi
    cecho " > Extract check_nwc_health" green
    folder=$(ls -1 | grep "^lausser-check_nwc_health")
    if [ ! -z "$folder" ]
    then
        rm -Rf lausser-check_nwc_health* >> /tmp/shinken.install.log 2>&1
    fi
    tar zxvf check_nwc_health.tar.gz >> /tmp/shinken.install.log 2>&1
    folder=$(ls -1 | grep "^lausser-check_nwc_health")
    cd $folder 
    cecho " > Build check_nwc_health.pl" green 
    autoreconf >> /tmp/shinken.install.log 2>&1
    ./configure --with-nagios-user=$SKUSER --with-nagios-group=$SKGROUP --enable-perfdata --enable-extendedinfo --prefix=$TARGET >> /tmp/shinken.install.log 2>&1
    make >> /tmp/shinken.install.log 2>&1
    cecho " > Install check_nwc_health.pl" green 
    make install >> /tmp/shinken.install.log 2>&1
}

# CHECK_EMC_CLARIION
function install_check_emc_clariion(){

    cadre "Install check_emc_clariion plugin from netways" green

    cecho " You will need the DELL/EMC Navisphere agent in order to use this
plugin. Ask your vendor to know how to get it." yellow
    cecho " You should also customize the navisphere agent path in the plugin" yellow
    read taste

    if [ "$CODE" == "REDHAT" ]
    then
        if [ ! -z "$CHECKEMCYUMPKG" ]
        then 
            cecho " > Installing prerequisites" green 
            yum install -yq $CHECKEMCYUMPKG  >> /tmp/shinken.install.log 2>&1 
        fi
    else
        if [ ! -z "$CHECKEMCAPTPKG" ]
        then 
            cecho " > Installing prerequisites" green 
            apt-get -y install $CHECKEMCAPTPKG >> /tmp/shinken.install.log 2>&1 
        fi
    fi

    if [ $? -ne 0 ]
    then
        cecho " > Error while installing prerequisites" red
        exit 2
    fi

    cd /tmp

    if [ ! -f "/tmp/check_emc.zip" ]
    then
        cecho " > Downloading check_emc.zip" green
        wget $WGETPROXY $CHECKEMC  >> /tmp/shinken.install.log 2>&1     
        if [ $? -ne 0 ]
        then
            cecho " > Error while downloading check_emc.zip" red
            exit 2
        fi
    fi

    cecho " > Extract check_emc.zip" green
    if [ -d check_emc ] 
    then 
        rm -Rf check_emc
    fi
    unzip check_emc.zip >> /tmp/shinken.install.log 2>&1
    if [ $? -ne 0 ]
    then
        cecho " > Error while trying to extract check_emc.zip" red
        exit 2
    fi
  
    cecho " > Install check_emc_clariion.pl" green 
    cd check_emc 
    mv check_emc_clariion.pl $TARGET/libexec/
    chmod +x $TARGET/libexec/check_emc_clariion.pl    
    chown $SKUSER:$SKGROUP $TARGET/libexec/check_emc_clariion.pl
}

# CHECK_ESX3
function install_check_esx3(){

    cadre "Install check_esx3 plugin from op5" green

    if [ "$CODE" == "REDHAT" ]
    then
        cecho " > Installing prerequisites" green 
        # because redhat package nagios-plugins-perl does not ship all files from Nagios::plugins
        yum install -yq $NAGPLUGYUMPKGS  >> /tmp/shinken.install.log 2>&1 
        cd /tmp
        wget $WGETPROXY $NAGPLUGPERL >> /tmp/shinken.install.log 2>&1
        tar zxvf $(echo $NAGPLUGPERL | awk -F "/" '{print $NF}') >> /tmp/shinken.install.log 2>&1
        cd  $(echo $NAGPLUGPERL | awk -F "/" '{print $NF}' |sed -e "s/\.tar\.gz//g") >> /tmp/shinken.install.log 2>&1
        perl Makefile.PL >> /tmp/shinken.install.log 2>&1
        make >> /tmp/shinken.install.log 2>&1
        if [ $? -ne 0 ]
        then
            cecho " > Error while building Nagios::Plugins perl modules" red
            exit 2
        fi    
        make install >> /tmp/shinken.install.log 2>&1
        yum install -yq $VSPHERESDKYUMPKGS  >> /tmp/shinken.install.log 2>&1 
    else
        cecho " > Installing prerequisites" green 
        apt-get -y install $VSPHERESDKAPTPKGS >> /tmp/shinken.install.log 2>&1 
    fi
    cd /tmp

    if [ ! -f "/tmp/VMware-vSphere-SDK-for-Perl-$VSPHERESDKVER.$ARCH.tar.gz" ]
    then
        cecho " > Downloading VSPHERE SPHERE SDK FOR PERL" green
        wget $WGETPROXY $VSPHERESDK  >> /tmp/shinken.install.log 2>&1     
        if [ $? -ne 0 ]
        then
            cecho " > Error while downloading vsphere sdk for perl" red
            exit 2
        fi
    fi

    cecho " > Extracting vsphere sdk for perl" green
    if [ -d "/tmp/vmware-vsphere-cli-distrib" ] 
    then
        cecho " > Removing old building folder" green
        rm -Rf vmware-vsphere-cli-distrib
    fi
    tar zxvf VMware-vSphere-SDK-for-Perl-$VSPHERESDKVER.$ARCH.tar.gz  >> /tmp/shinken.install.log 2>&1 
    cd vmware-vsphere-cli-distrib 
    cecho " > Building vsphere sdk for perl" green
    perl Makefile.PL >> /tmp/shinken.install.log 2>&1 
    make >> /tmp/shinken.install.log 2>&1 
    cecho " > Installing vsphere sdk for perl" green
    make install >> /tmp/shinken.install.log 2>&1 

    cd /tmp
    cecho " > Getting check_esx3 plugin from op5" green
    wget $WGETPROXY $CHECK_ESX3_SCRIPT -O check_esx3.pl >> /tmp/shinken.install.log 2>&1 
    mv check_esx3.pl $TARGET/libexec/check_esx3.pl
    chmod +x $TARGET/libexec/check_esx3.pl    
    chown $SKUSER:$SKGROUP $TARGET/libexec/check_esx3.pl
        
}

# NAGIOS-PLUGINS
function install_nagios-plugins(){
    cadre "Install nagios plugins" green

    if [ "$CODE" == "REDHAT" ]
    then
        cecho " > Installing prerequisites" green
        yum install -yq $NAGPLUGYUMPKG  >> /tmp/shinken.install.log 2>&1 
    else
        cecho " > Installing prerequisites" green 
        DEBIAN_FRONTEND=noninteractive apt-get -y install $NAGPLUGAPTPKG >> /tmp/shinken.install.log 2>&1 
    fi
    cd /tmp
    if [ ! -f "nagios-plugins-$NAGPLUGVERS.tar.gz" ]
    then
        cecho " > Getting nagios-plugins archive" green
        wget $WGETPROXY $NAGPLUGBASEURI >> /tmp/shinken.install.log 2>&1 
    fi
    cecho " > Extract archive content " green
    rm -Rf nagios-plugins-$NAGPLUGVERS
    tar zxvf nagios-plugins-$NAGPLUGVERS.tar.gz >> /tmp/shinken.install.log 2>&1 
    cd nagios-plugins-$NAGPLUGVERS
    cecho " > Configure source tree" green
    ./configure --with-nagios-user=$SKUSER --with-nagios-group=$SKGROUP --enable-libtap --enable-extra-opts --prefix=$TARGET --enable-perl-modules >> /tmp/shinken.install.log 2>&1 
    cecho " > Building ...." green
    make >> /tmp/shinken.install.log >> /tmp/shinken.install.log  2>&1 
    cecho " > Installing" green
    make install >> /tmp/shinken.install.log >> /tmp/shinken.install.log  2>&1 
    cp contrib/check_mem.pl $TARGET/libexec >> /tmp/shinken.install.log  2>&1 
    chmod +x $TARGET/libexec/check_mem.pl >> /tmp/shinken.install.log  2>&1
    chown $SKUSER:$SKGROUP $TARGET/libexec/check_mem.pl >> /tmp/shinken.install.log 2>&1
}

# MANUBULON SNMP PLUGINS 
function install_manubulon(){
    cadre "Install manubulon plugins" green

    if [ "$CODE" == "REDHAT" ]
    then
        cecho " > Installing prerequisites" green
        yum install -yq $MANUBULONYUMPKG  >> /tmp/shinken.install.log 2>&1 
    else
        cecho " > Installing prerequisites" green 
        apt-get -y install $MANUBULONAPTPKG >> /tmp/shinken.install.log 2>&1 
    fi
    cd /tmp

    # check if utils.pm is there
    if [ ! -f $TARGET/libexec/utils.pm ]
    then
        cecho " > Unable to find utils.pm. You should install nagios-plugins first (./shinken.sh -p nagios-plugins)" red
        exit 2
    fi

    archive=$(echo $MANUBULON | awk -F/ '{print $NF}')
    folder=nagios_plugins
    if [ ! -f "$archive" ]
    then
        cecho " > Getting manubulon archive" green
        wget $WGETPROXY $MANUBULON >> /tmp/shinken.install.log 2>&1 
    fi
    cecho " > Extract archive content " green
    if [ -d $folder ]
    then
        rm -Rf $folder 
    fi
    tar zxvf $archive >> /tmp/shinken.install.log 2>&1 
    cd $folder 
    cecho " > Relocate libs" green
    for s in $(ls -1 /tmp/$folder/*.pl)
    do
        cecho " => Processing $s" green
        sed -i "s#/usr/local/nagios/libexec#"$TARGET"/libexec#g" $s
        cecho " => Installing $s" green
        cp $s $TARGET/libexec
    done
}

# CHECK_WMI_PLUS
function install_check_wmi_plus(){
    cadre "Install check_wmi_plus" green

    if [ "$CODE" == "REDHAT" ]
    then
        cecho " > Installing prerequisites" green 
        yum -yq install $WMICYUMPKG >> /tmp/shinken.install.log 2>&1 
    else
        cecho " > Installing prerequisites" green 
        apt-get -y install $WMICAPTPKG >> /tmp/shinken.install.log 2>&1
    fi 
    cd /tmp
    cecho " > Downloading wmic" green
    filename=$(echo $WMIC | awk -F"/" '{print $NF}')
    if [ ! -f $(echo $filename | sed -e "s/\.bz2//g") ]
    then
        wget $WGETPROXY $WMIC >> /tmp/shinken.install.log 2>&1 
        bunzip2 $filename
    else
        rm -Rf $(echo $filename | sed -e "s/\.tar//g")
    fi
    if [ $? -ne 0 ]
    then
        cecho " > Error while downloading $filename" red
        exit 2
    fi
    cecho " > Extracting archive " green
    tar xvf $(echo $filename| sed -e "s/\.bz2//g") >> /tmp/shinken.install.log 2>&1 
    cd $(echo $filename | sed -e "s/\.tar\.bz2//g")
    cecho " > Building wmic" green
    make >> /tmp/shinken.install.log 2>&1 
    if [ $? -ne 0 ] 
    then
        cecho " > Error while building wmic" red
        exit 2
    fi
    cecho " > Installing wmic" green
    cp Samba/source/bin/wmic $TARGET/libexec/
    chown $SKUSER:$SKGROUP Samba/source/bin/wmic
    cd /tmp
    cecho " > Downloading check_wmi_plus" green
    filename=$(echo $CHECKWMIPLUS | awk -F"/" '{print $NF}')
    folder=$(echo $filename | sed -e "s/\.tar\.gz//g")
    if [ ! -f "$filename" ]
    then
        wget $WGETPROXY $CHECKWMIPLUS >> /tmp/shinken.install.log 2>&1  
    fi
    cecho " > Extracting archive" green
    tar zxvf $filename >> /tmp/shinken.install.log 2>&1 
    cecho " > Installing plugin" green
    cp check_wmi_plus.conf.sample $TARGET/libexec/check_wmi_plus.conf 
    cp check_wmi_plus.pl $TARGET/libexec/check_wmi_plus.pl
    cp -R /tmp/check_wmi_plus.d $TARGET/libexec/
    chown $SKUSER:$SKGROUP $TARGET/libexec/check_wmi_plus* 
    cecho " > configuring plugin" green
    sed -i "s#/usr/lib/nagios/plugins#"$TARGET"/libexec#g" $TARGET/libexec/check_wmi_plus.conf
    sed -i "s#/bin/wmic#"$TARGET"/libexec/wmic#g" $TARGET/libexec/check_wmi_plus.conf
    sed -i "s#/opt/nagios/bin/plugins#"$TARGET"/libexec#g" $TARGET/libexec/check_wmi_plus.pl
    sed -i "s#/usr/lib/nagios/plugins#"$TARGET"/libexec#g" $TARGET/libexec/check_wmi_plus.pl
}

# CHECK_ORACLE_HEALTH
function install_check_oracle_health(){
    cadre "Install nagios plugins" green

    if [ -z "$ORACLE_HOME" ]
    then
        cadre "WARNING YOU SHOULD INSTALL ORACLE INSTANT CLIENT FIRST !!!!" yellow
        cecho " > Download the oracle instant client there (basic AND sdk AND sqlplus) : " yellow
        cecho " > 64 bits : http://www.oracle.com/technetwork/topics/linuxx86-64soft-092277.html" yellow
        cecho " > 32 bits : http://www.oracle.com/technetwork/topics/linuxsoft-082809.html" yellow
        cecho " > Set the ORACLE_HOME environment variable (better to set it in the bashrc)" yellow
        cecho " > Set LD_LIBRARY_PATH to ORACLE_HOME (or better create a config file in /etc/ld.so.conf) then run ldconfig" yellow
        cecho " > press ENTER to continue or CTRL+C to abort" yellow
        exit 2
    fi

    if [ "$CODE" == "REDHAT" ]
    then
        cecho " > Installing prerequisites" green 
        apt-get -y install $CHECKORACLEHEALTHYUMPKG >> /tmp/shinken.install.log 2>&1 
    else
        cecho " > Installing prerequisites" green 
        apt-get -y install $CHECKORACLEHEALTHAPTPKG >> /tmp/shinken.install.log 2>&1 
    fi
    cecho " > Installing cpan prerequisites" green
    cd /tmp
    for m in $CHECKORACLEHEALTHCPAN
    do
        filename=$(echo $m | awk -F"/" '{print $NF}')
        if [ ! -f "$filename" ]
        then
            wget $WGETPROXY $m >> /tmp/shinken.install.log 2>&1 
            if [ $? -ne 0 ]
            then
                cecho " > Error while downloading $m" red
                exit 2
            fi
        fi    
        tar zxvf $filename  >> /tmp/shinken.install.log 2>&1 
        cd $(echo $filename | sed -e "s/\.tar\.gz//g")
        perl Makefile.PL >> /tmp/shinken.install.log 2>&1 
        make >> /tmp/shinken.install.log 2>&1 
        if [ $? -ne 0 ]
        then
            cecho " > There was an error building module" red
            exit 2
        fi
        make install  >> /tmp/shinken.install.log 2>&1 
    done
    cd /tmp
    cecho " > Downloading check_oracle_health" green
    wget $WGETPROXY $CHECKORACLEHEALTH >> /tmp/shinken.install.log 2>&1 
    if [ $? -ne 0 ]
    then
        cecho " > Error while downloading $filename" red
        exit 2
    fi
    cecho " > Extracting archive " green
    filename=$(echo $CHECKORACLEHEALTH | awk -F"/" '{print $NF}')
    tar zxvf $filename >> /tmp/shinken.install.log 2>&1 
    cd $(echo $filename | sed -e "s/\.tar\.gz//g")
    ./configure --prefix=$TARGET --with-nagios-user=$SKUSER --with-nagios-group=$SKGROUP --with-mymodules-dir=$TARGET/libexec --with-mymodules-dyn-dir=$TARGET/libexec --with-statefiles-dir=$TARGET/var/tmp >> /tmp/shinken.install.log 2>&1 
    cecho " > Building plugin" green
    make >> /tmp/shinken.install.log 2>&1 
    if [ $? -ne 0 ] 
    then
        cecho " > Error while building check_oracle_health module" red
        exit 2
    fi
    make check >> /tmp/shinken.install.log 2>&1     
    if [ $? -ne 0 ]
    then
        cecho " > Error while building check_oracle_health module" red
        exit 2
    fi
    cecho " > Installing plugin" green
    make install >> /tmp/shinken.install.log 2>&1
    mkdir -p $TARGET/var/tmp >> /tmp/shinke.install.log 2>&1 
}
# CHECK_NETAPP2

function install_check_netapp2(){
    cadre "Install check_netapp2" green

    if [ "$CODE" == "REDHAT" ]
    then
        cecho " > Installing prerequisites" green
        yum -yq install $CHECKNETAPP2YUMPKGS >> /tmp/shinken.install.log
    else
        cecho " > Installing prerequisites" green
        apt-get -y install $CHECKNETAPP2APTPKGS >> /tmp/shinken.install.log
    fi
    cd /tmp
    cecho " > Downloading check_netapp2" green
    wget $WGETPROXY -O check_netapp2 $CHECKNETAPP2 >> /tmp/shinken.install.log 2>&1 
    if [ $? -ne 0 ]
    then
        cecho " > Error while downloading check_netapp2" red
        exit 2
    fi
    cecho " > Installing plugin" green
    # fuckin assholes that upload perl scripts edited with notepad or so
    perl -p -e 's/\r$//' < check_netapp2 > check_netapp2.pl
    chmod +x check_netapp2.pl >> /tmp/shinken.install.log 2>&1
    chown $SKUSER:$SKGROUP check_netapp2.pl >> /tmp/shinken.install.log 2>&1
    cp -p check_netapp2.pl $TARGET/libexec/check_netapp2 >> /tmp/shinken.install.log 2>&1 
    sed -i "s#/usr/local/nagios/libexec#"$TARGET"/libexec#g" $TARGET/libexec/check_netapp2 >> /tmp/shinken.install.log 2>&1
}

# CHECK_MYSQL_HEALTH
function install_check_mysql_health(){
    cadre "Install check_mysql_health" green

    if [ "$CODE" == "REDHAT" ]
    then
        cecho " > Installing prerequisites" green
        yum -yq install $CHECKMYSQLHEALTHYUMPKG >> /tmp/shinken.install.log
    else
        cecho " > Installing prerequisites" green
        apt-get -y install $CHECKMYSQLHEALTHAPTPKG >> /tmp/shinken.install.log
    fi
    cd /tmp
    cecho " > Downloading check_mysql_health" green
    wget $WGETPROXY $CHECKMYSQLHEALTH >> /tmp/shinken.install.log 2>&1 
    if [ $? -ne 0 ]
    then
        cecho " > Error while downloading $filename" red
        exit 2
    fi
    cecho " > Extracting archive " green
    filename=$(echo $CHECKMYSQLHEALTH | awk -F"/" '{print $NF}')
    tar zxvf $filename >> /tmp/shinken.install.log 2>&1 
    cd $(echo $filename | sed -e "s/\.tar\.gz//g")
    ./configure --prefix=$TARGET --with-nagios-user=$SKUSER --with-nagios-group=$SKGROUP --with-mymodules-dir=$TARGET/libexec --with-mymodules-dyn-dir=$TARGET/libexec --with-statefiles-dir=$TARGET/var/tmp >> /tmp/shinken.install.log 2>&1 
    cecho " > Building plugin" green
    make >> /tmp/shinken.install.log 2>&1 
    if [ $? -ne 0 ] 
    then
        cecho " > Error while building check_mysql_health module" red
        exit 2
    fi
    make check >> /tmp/shinken.install.log 2>&1     
    if [ $? -ne 0 ]
    then
        cecho " > Error while building check_mysql_health module" red
        exit 2
    fi
    cecho " > Installing plugin" green
    make install >> /tmp/shinken.install.log 2>&1 
}


function usage(){
echo "Usage : shinken -k | -i | -w | -d | -u | -b | -r | -l | -c | -h | -a | -z [poller|centreon] | -e daemons | -p plugins [plugname]
    -k  Kill shinken
    -i  Install shinken
    -w  Remove demo configuration 
    -d  Remove shinken
    -u  Update an existing shinken installation
    -v  purge livestatus sqlite db and shrink sqlite db
    -b  Backup shinken configuration plugins and data
    -r  Restore shinken configuration plugins and data
    -l  List shinken backups
    -c  Compress rotated logs
    -e  Which daemons to keep enabled at boot time
    -z  This is a really special usecase that allow to install shinken on Centreon Enterprise Server in place of nagios
    -p  Install plugins or addons (args should be one of the following : 
        check_esx3
        nagios-plugins
        check_oracle_health
        check_mysql_health
        check_wmi_plus
        check_mongodb
        check_emc_clariion
        check_nwc_health
        check_hpasm
        manubulon (snmp plugins)
        capture_plugin
        pnp4nagios
        multisite
    -h  Show help"
}

# Check if we launch the script with root privileges (aka sudo)
if [ "$UID" != "0" ]
then
        cecho "You should start the script with sudo!" red
        exit 1
fi

if [ ! -z "$PROXY" ]
then
    export http_proxy=$PROXY
    export https_proxy=$PROXY
    export WGETPROXY=" -Y on "
fi

while getopts "kidubcr:lz:hsvp:we:" opt; do
    case $opt in
        p)
            if [ "$OPTARG" == "check_esx3" ]
            then
                install_check_esx3
                exit 0
            elif [ "$OPTARG" == "nagios-plugins" ]
            then
                install_nagios-plugins
                exit 0
            elif [ "$OPTARG" == "check_oracle_health" ]
            then
                install_check_oracle_health
                exit 0
            elif [ "$OPTARG" == "check_mysql_health" ]
            then
                install_check_mysql_health
                exit 0
            elif [ "$OPTARG" == "capture_plugin" ]
            then
                install_capture_plugin
                exit 0
            elif [ "$OPTARG" == "check_wmi_plus" ]
            then
                install_check_wmi_plus
                exit 0
            elif [ "$OPTARG" == "check_mongodb" ]
            then
                install_check_mongodb
                exit 0
            elif [ "$OPTARG" == "check_emc_clariion" ]
            then
                install_check_emc_clariion
                exit 0
            elif [ "$OPTARG" == "check_nwc_health" ]
            then
                install_check_nwc_health
                exit 0
            elif [ "$OPTARG" == "manubulon" ]
            then
                install_manubulon
                exit 0
            elif [ "$OPTARG" == "check_hpasm" ]
            then
                install_check_hpasm
                exit 0
            elif [ "$OPTARG" == "check_netapp2" ]
            then
                install_check_netapp2
                exit 0
            elif [ "$OPTARG" == "pnp4nagios" ]
            then
                install_pnp4nagios
                exit 0
            elif [ "$OPTARG" == "multisite" ]
            then
                install_multisite
                exit 0
            elif [ "$OPTARG" == "nagvis" ]
            then
                install_nagvis
                exit 0
            else
                cecho " > Unknown plugin $OPTARG" red
            fi
            ;;
        j)
            addpoller "$OPTARG"
            exit 0
            ;;
        e)
            setdaemons "$OPTARG"
            exit 0
            ;;
        w)
            cleanconf    
            exit 0
            ;;
        z)
            mode=$OPTARG
            cleanconf
            disablenagios
            fixsudoers
            if [ "$mode" = "centreon" ]
            then
                fixcentreondb
                fixforfan
                enablendodb
                #enableretention
                enableperfdata
                setdaemonsaddresses
                enableCESCentralDaemons
                #fixHtpasswdPath
                #addCESPollers
            else
                enableCESPollerDaemons
            fi
            exit 0
            ;;
        s)
            rheldvd    
            exit 0
            ;;
        v)
            purgeSQLITE    
            exit 0
            ;;

        # Sugg :
        # Code never reached, case already done above.
        # Remove this?
        z)
            check_distro
            exit 0
            ;;
        k)
            skill
            exit 0
            ;;
        i)
            FROMSRC=1
            sinstall 
            fixHtpasswdPath
            exit 0
            ;;
        d)
            remove 
            exit 0
            ;;
        u)
            supdate 
            exit 0
            ;;
        b)
            backup 
            exit 0
            ;;
        r)
            restore $OPTARG 
            exit 0
            ;;
        l)
            backuplist 
            exit 0
            ;;
        c)
            compresslogs
            exit 0
            ;;
        h)
            shelp    
            exit 0
            ;;
    esac
done
usage
exit 0

