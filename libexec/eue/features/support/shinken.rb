require "rubygems"
require 'cucumber/formatter/console'
require 'date'
require 'mongo'
formater_path = File.expand_path(File.dirname(__FILE__)+"/../../features/support")        
require "#{formater_path}/commons.rb"


module Eue
    class Shinken < Commons

      def initialize(step_mother, io, options={})

          base_path = File.expand_path(File.dirname(__FILE__)+"/../../")        
          project = ""

          ARGV.each do | element |
              if element.index(/\.feature/)
                  fullname=element.split("/")[element.split("/").length-1]
                  project = fullname.split(".")[0]
                  break
              end
          end

          if project == ""
              exit 2
          end

          @@params = IniFile.new(base_path+"/#{project}.ini", :parameter => '=')
          puts @@params
          @@connection = nil
          @@db = nil
          @@collection = nil
          @@video = ""
          connect()
      end

      def after_feature(feature)
          if @@params["media"]["capturevideo"].to_i == 1
            media = @@params["media"]["path"]
            @@video = "#{@@start_time.to_i}_#{normalizestring(normalizestring(@@params["application"]["name"]))}_#{normalizestring(@@feature)}.#{@@params['media']['videoextension']}"
            begin
              $headless.video.stop_and_save("#{media}/#{@@video}")
            rescue

            end
            videodata = File.open("#{media}/#{@@video}")
            dbgrid = @@connection.db(@@params["mongo"]["dbgrid"])        
            fsgrid = Mongo::GridFileSystem.new(dbgrid)
            fsgrid.open(@@video, "w") do |f|
              f.write videodata
            end         
            #File.delete("#{media}/#{@@video}")
          end
          print_summary()
      end

      private

      def connect()
        begin
          @@connection = Mongo::Connection.new(@@params["mongo"]["host"],@@params["mongo"]["port"].to_i)
          # puts "Connected to %s %s"  % [@@params["mongo"]["host"],@@params["mongo"]["port"]]
        rescue
          puts "Unable to connect to mongodb server %s %s" % [@@params["mongo"]["host"],@@params["mongo"]["port"]]
          exit 2
        end

        begin
          @@db = @@connection.db(@@params["mongo"]["db"])
          # puts "%s db opened" % @@params["mongo"]["db"]
        rescue
          puts "Unable to connect to database %s" % @@params["mongo"]["db"]
          exit 2
        end

        begin
          @@collection = @@db.collection(@@params["mongo"]["collection"])
          # puts "%s collection opened" % @@params["mongo"]["collection"]
        rescue
          puts "Unable to open collection %s" % @@params["mongo"]["collection"]
          exit 2
        end

      end

      def insert_document(document)
        id = @@collection.insert(document)
        return id
      end

      def print_summary

        key = "%s.%s.%s.%s.%s.%s" % [ 
                  @@start_time.to_i.to_s,
                  normalizestring(@@params["application"]["name"]),
                  normalizestring(@@feature),
                  normalizestring(@@params["robot"]["os"]),
                  normalizestring(@@params["browser"]["name"]),
                  normalizestring(@@params["robot"]["localization"])
        ]

        document = {
          "key" => key,
          "application" => @@params["application"]["name"],
          "application_code" => normalizestring(@@params["application"]["name"]),
          "feature" => @@feature,
          "start_time" => @@params["mongo"]["dateformat"] == "native" ? @@start_time : @@start_time.to_i,
          "description" => @@description,
          "platform" => {
            "os" => @@params["robot"]["os"],
            "localization" => @@params["robot"]["localization"],
            "browser" => @@params["browser"]["name"]
          },
          "dbmedia" => @@params["mongo"]["dbmedia"],
          "screenshots_path" => @@params["media"]["path"],
          "video" => @@video,
          "scenarios" => @@scenarios,
          "robot" => @@params["robot"]["name"]
        }

        id = insert_document(document)

        ##puts @@document.to_json.to_s.gsub("{","{\n").gsub("}","\n}\n").gsub(",",",\n")
        output_shinken(key)
      end

      def take_screenshot(feat, scenario, step, scenario_index, step_index)
        if step.to_s != ""
          feature,*descritption = feat.split("\n")
          screenshot_file = "#{@@cur_scenario_start.to_i}_#{normalizestring(feature)}_%04d_#{normalizestring(scenario)}_%04d_#{normalizestring(step)}.png" % [scenario_index,step_index]
        else
          feature,*descritption = feat.split("\n")
          screenshot_file = "#{@@cur_scenario_start.to_i}_#{normalizestring(feature)}_%04d_#{normalizestring(scenario)}.png" % scenario_index
        end          
        screenshot = "#{@@params["media"]["path"]}/#{screenshot_file}"
        Browser.driver.save_screenshot(screenshot)

        image = File.open(screenshot)
        dbgrid = @@connection.db(@@params["mongo"]["dbgrid"])        
        fsgrid = Mongo::GridFileSystem.new(dbgrid)
        fsgrid.open(screenshot_file, "w") do |f|
          f.write image
        end         
        #File.delete(screenshot)
        return screenshot_file      
      end

    end
end

