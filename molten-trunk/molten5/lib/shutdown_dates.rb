class  ShutdownDates
  # Used to manage the shutdown dates from AppConstants and AppSetting. 
  def start_dates
    begin
      num_dates = AppSetting.config("SHUTDOWN_DATES").to_i
    rescue
      num_dates = 0
    end
    dates = []
    0.upto(num_dates) { |i| 
      puts i
      begin
        begin_date = AppSetting.config("SHUTDOWN_DATE_RANGE{i}")
      rescue
        begin_date = ''
      end
      if (begin_date.length == 0)
        begin_date = AppConstants::SHUTDOWN_DATES[0]
      else
        begin_date = Date.strptime(begin_date.split(',')[0],fmt='%m/%d/%Y')
      end
      dates.push(begin_date)
    }
    return dates
  end

  def end_dates
    begin
      num_dates = AppSetting.config("SHUTDOWN_DATES").to_i
    rescue
      num_dates = 0
    end
    dates = []
    0.upto(num_dates) { |i| 
      puts i
      begin
        end_date = AppSetting.config("SHUTDOWN_DATE_RANGE{i}")
      rescue
        end_date = ''
      end
      if (end_date.length == 0)
        end_date = AppConstants::SHUTDOWN_DATES[-1]
      else
        end_date = Date.strptime(end_date.split(',')[-1],fmt='%m/%d/%Y')
      end
      dates.push(end_date)
    }
    return dates
  end

  def messages
    begin
      num_dates = AppSetting.config("SHUTDOWN_DATES").to_i
    rescue
      num_dates = 0
    end
    the_messages = []
    0.upto(num_dates) { |i| 
      puts i
      begin
        the_message = AppSetting.config("SHUTDOWN_MESSAGE{i}")
      rescue
        the_message = ''
      end
      if (the_message.length == 0)
        the_message = AppConstants::SHUTDOWN_NOTICE
      end
      the_messages.push(the_message)
    }
    return the_messages
  end

  def alt_messages
    begin
      num_dates = AppSetting.config("SHUTDOWN_DATES").to_i
    rescue
      num_dates = 0
    end
    the_messages = []
    0.upto(num_dates) { |i| 
      puts i
      begin
        the_message = AppSetting.config("ALT_SHUTDOWN_MESSAGE{i}")
      rescue
        the_message = ''
      end
      if (the_message.length == 0)
        the_message = AppConstants::ALT_SHUTDOWN_NOTICE
      end
      the_messages.push(the_message)
    }
    return the_messages
  end
end