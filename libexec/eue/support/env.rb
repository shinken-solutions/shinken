require 'rubygems'
require 'watir-webdriver'
require 'watir-webdriver/wait'
require 'headless'
require 'inifile'
require 'date'
require 'unicode'

# base path
base_path = File.expand_path(File.dirname(__FILE__)+"/../")
# puts base_path  
project = ""

ARGV.each do | element |
    if element.index(/\.feature/)
        fullname=element.split("/")[element.split("/").length-1]
        project = fullname.split(".")[0]
        break
    end
end

if project == ""
    # puts "No project defined"
    exit 2
end

# load params from ini file
params = IniFile.new(base_path+"/#{project}.ini", :parameter => '=')

if not defined?($Index)
	$Index = 0
end

# linux only
mode = 					params["execution"]["mode"]
headless_resolution= 	params["execution"]["resolution"]
headless_display=		params["execution"]["display"]
# firefox | ie | chrome
browser_name=			params["browser"]["name"]
# firefox only
if browser_name == "firefox"
	browser_path=		params["browser"]["path"]
else
	browser_path=		"default"
end

use_proxy=				params["browser"]["use_proxy"]
proxy_host=				params["browser"]["proxy_host"]
proxy_port=				params["browser"]["proxy_port"]
proxy_autourl=			params["browser"]["proxy_autourl"]
no_proxy=			    params["browser"]["no_proxy"]

# media
capture_path=			params["media"]["path"]
capture_screenshots=	params["media"]["capture"].to_i
capture_video=			params["media"]["capturevideo"].to_i
media_server_url=		params["media"]["url"]
capture_level=			params["media"]["capture_level"]

if browser_name == "phantomjs"
    # we do not need Xvfb for phantomjs
    mode = "visible"
end

if mode == "headless"
	display = headless_display
	if capture_video == 1
		$headless = Headless.new(
								:dimensions =>  headless_resolution, 
								:display => display,
								:video => {
									:codec => params["media"]["videocodec"],
									:tmp_file_path => "#{params['media']['path']}/tmp_feature.#{params['media']['videoextension']}",
									:log_file_path => "/tmp/ffmpeg.log"
									}
								)           
		$headless.start
		$headless.video.start_capture
	else
		$headless = Headless.new(
								:dimensions =>  headless_resolution, 
								:display => display
								)           
		$headless.start
	end

elsif mode == "visible"

else
	puts "Unsuported mode %s ! " % mode
	Process.exit(2)	
end

# Sikuli XMLRPC server and client instance
if params['sikuli']['enabled'] != "false"
        require base_path+'/support/sikuli.rb'
        params['sikuli']['project'] = "#{project}.sikuli"
        sk = Sikuli.new(params['sikuli']['java'],params['sikuli']['path'],base_path,params['sikuli']['project'],params['sikuli']['host'],params['sikuli']['port'],params['sikuli']['redirect'])
        sk.start_server
        sk.start_client
end

if browser_name == "firefox"
	if browser_path != "default"
		Selenium::WebDriver::Firefox.path = browser_path
	end

	if params["browser"]["profile"] != ""
		# TODO : load specific profile
	end

	profile = Selenium::WebDriver::Firefox::Profile.new
	profile.native_events = false

	if use_proxy == "1"
		if proxy_autourl != ""
			proxy.setProxyAutoconfigUrl(proxy_autourl)
		else
			profile["network.proxy.type"] = 1 
			profile["network.proxy.http"] = proxy_host
			profile["network.proxy.http_port"] = proxy_port.to_i
			profile["network.proxy.no_proxies_on"] = no_proxy
		end
	end

	Browser = Watir::Browser.new(:firefox, :profile => profile)	
	Browser.driver.manage.timeouts.implicit_wait=3
elsif browser_name == "chrome"
	switches_array = ["--ignore-certificate-errors", "--disable-popup-blocking", "--disable-translate"]
	if use_proxy == "1"
		 if proxy_autourl != ""
		 	switches_array << "--proxy-pac-url=#{proxy_autourl}"
		 else
		 	switches_array << "--proxy-server=#{proxy_host}:#{proxy_port}"
		 end
	end
	Browser = Watir::Browser.new(:chrome, :switches => switches_array)
	Browser.driver.manage.timeouts.implicit_wait=3
elsif browser_name == "phantomjs"
	switches_array = ["--disk-cache=false", "--ignore-ssl-errors=true","--load-images=true"]
	if use_proxy == "1"
        switches_array << "--proxy=#{proxy_host}:#{proxy_port}"
	end
	Browser = Watir::Browser.new(:phantomjs, :switches => switches_array)
else
	puts "Unsuported browser %s ! " % browser_name
	Process.exit(2)
end


Before do |scenario|
    @browser = Browser
    if params['sikuli']['enabled'] != "false"
      @sikuli = sk
    end
end

at_exit do
	Browser.close
    if params['sikuli']['enabled'] != "false"
            sk.stop_server
    end
end
