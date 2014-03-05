class Commons

      @@params =                     nil
      @@start_time =                 nil
      @@feature =                    nil
      @@description =                nil
      @@scenarios =                  {}
      @@cur_scenario =               nil
      @@cur_scenario_name =          nil
      @@cur_scenario_steps_failed =  0
      @@cur_scenario_steps_succeed = 0
      @@cur_scenario_start =         nil
      @@cur_scenario_steps =         []
      @@step_index =                 0
      @@scenario_index =             0
      @@steps_failed_detail =        []
      @@cur_step_start_time =        nil

      @@feature_video =              nil

      @@robot_name =                 nil
      @@environment =                nil
      @@os =                         nil
      @@localization =               nil
      @@navigator =                  nil
      @@feature_state =              0

    def after_step_result(keyword, step_match, multiline_arg, status, exception, source_indent, background,xx)
      if status.to_s == "passed"
        @@cur_scenario_steps_succeed += 1
      else
        @@cur_scenario_steps_failed += 1
      end
    end

    def before_feature(feature)
        feat,*desc = feature.name.split(/\n/)        
        @@feature = feat
        @@description = *desc
        @@start_time = Time.now
    end

    # before scenario execution
    def scenario_name(keyword, name, file_colon_line, source_indent)
        @@cur_scenario_start = Time.now
        @@cur_scenario = normalizestring(name)
        @@cur_scenario_name = name
        @@scenarios[@@cur_scenario] = {}
        @@scenario_index += 1
        @@step_index = 1 
    end

    # after scenario execution
    def after_steps(steps)
        if @@params["media"]["capture"].to_i == 1 && @@params["media"]["capture_level"] == "scenario"
          screenshot = take_screenshot(@@feature, @@cur_scenario, "", @@scenario_index, 0)
        else
          screnshot = nil
        end  
        @@scenarios[@@cur_scenario] = {
                                      "name" => @@cur_scenario_name,
                                      "failed_steps" => @@steps_failed_detail, 
                                      "index" => @@scenario_index ,
                                      "status" => @@cur_scenario_steps_failed > 0 ? 2 : 0, 
                                      "failed" => @@cur_scenario_steps_failed, 
                                      "succeed" => @@cur_scenario_steps_succeed, 
                                      "duration" => Time.now - @@cur_scenario_start, 
                                      "steps" => @@cur_scenario_steps,
                                      "start_time" => @@params["mongo"]["dateformat"] == "native" ? @@cur_scenario_start : @@cur_scenario_start.to_i,
                                      "screenshot" => screenshot
                                    }
        @@steps_failed_detail = []
        @@cur_scenario = nil
        @@cur_scenario_name = nil
        @@cur_scenario_steps_failed = 0
        @@cur_scenario_steps_succeed = 0
        @@cur_scenario_steps = []
    end

    def before_step(step)
      @@cur_step_start_time = Time.now
    end

    def after_step(step)
      if @@params["media"]["capture"].to_i == 1 && @@params["media"]["capture_level"] == "step"
        screenshot = take_screenshot(@@feature, @@cur_scenario, "#{step.keyword}#{step.name.to_s}", @@scenario_index, @@step_index)
      else
        screenshot = nil        
      end          

      if @@params["security"]["hidepatterns"].to_s != ""
        stepdef = "#{step.keyword} #{step.name}"
        patterns = @@params["security"]["hidepatterns"].to_s.split(@@params["security"]["patternseparator"])
        index = 0
        patterns.each do |pattern|
          results = /#{pattern}/.match(stepdef)
          if results and results.to_a.count() > 0
            marray = results.to_a.pop(results.to_a.count()-1)
            marray.each do | tohide |
              stepdef = stepdef.gsub(tohide,"*******")
            end
          end
          index += 1
        end
      else
        stepdef = "#{step.keyword} #{step.name}"
      end

      if step.status.to_s == "failed"
        @@feature_state = 2
        @@steps_failed_detail << stepdef          
      end

      @@cur_scenario_steps << {
        "index" => @@step_index,
        "step" => stepdef,
        "status" => step.status.to_s == "passed" ? 0 : 2,
        "start_time" => @@params["mongo"]["dateformat"] == "native" ? @@cur_step_start_time : @@cur_step_start_time.to_i,
        "screenshot" => screenshot 
      }
      @@step_index += 1

    end

    def result_data()
        status = 0
        failed = ""
        duration = 0
        total_failed = 0
        total_succeed = 0
        perfs = []
        @@scenarios.sort_by { | scenario,data | data["index"] }.each do | scenario,data |
          data = @@scenarios[scenario]
          status = 2 if data["status"].to_i == 2

          if data["status"].to_i != 0
            failed = "#{failed}, #{scenario} (#{data["failed_steps"].join(", ")})"
            total_failed += 1
          else
            total_succeed += 1
          end

          duration += data['duration']

          perfs.push("#{scenario}=#{data["duration"]}s")
        end

        return {  "status" => status, 
                  "failed" => failed, 
                  "total_failed" => total_failed, 
                  "total_succeed" => total_succeed, 
                  "duration" => duration,
                  "perfdata" => perfs }

    end

    def output_shinken(key)
        result = result_data()

        status = result["status"]
        failed = result["failed"]
        perfs = result["perfdata"]
        total_failed = result["total_failed"]
        total_succeed = result["total_succeed"]
        duration = result["duration"]        

        # key = "%s.%s.%s" % [ @@start_time.to_i.to_s,normalizestring(@@params["application"]["name"]),normalizestring(@@feature)]
        uri = "<a href=\"%s/%s\">%s</a>" % [@@params["shinken"]["base_uri"],key,@@feature]
        puts "[#{status == 2 ? "CRITICAL" : "OK"}] #{uri} #{failed} | scenarios_failed=#{total_failed} scenarios_succeed=#{total_succeed} scenarios_total=#{total_succeed+total_failed} total_time=#{duration}s #{perfs.join(" ")}"
        exit(status)
    end

    private

    def print_summary(source="global")
        if source == "feature"
          print_summary_feature
        elsif source == "scenario"
          print_summary_scenario
        elsif source == "step"
          print_summary_step
        elsif source == "global"
          print_summary_global
        else
          print 
        end
    end

    def print_summary_feature
      print
    end

    def print_summary_scenario
      print
    end

    def print_summary_step
      print
    end

    def print_summary_global
      print
    end

    def normalizestring(data)
      str = Unicode.normalize_KD(data).gsub(/[^\x00-\x7F]/n,'')
      str = str.gsub(/\W+/, '-').gsub(/^-+/,'').gsub(/-+$/,'').gsub(".","-")
      str = str.gsub(' ','_')
    end

end