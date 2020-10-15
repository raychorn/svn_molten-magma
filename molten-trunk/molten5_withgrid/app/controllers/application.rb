require_dependency 'authentication_system'

# Filters added to this controller will be run for all controllers in the application.
# Likewise, all the methods added will be available for all controllers.
class ApplicationController < ActionController::Base
  include AuthenticationSystem
  include ExceptionNotifiable
  # for testing in dev mode
  #local_addresses.clear
  
  before_filter :check_downtime
  before_filter :set_notice
  before_filter :pass_cookies

  def ajax_error(message = "An error has occurred")
    render :update do |page|
         page << "alert('#{message}');"
    end
  end
  
  # Sets +flash[:notice]+ equal to +param[:notice]+ if provided.
  def set_notice
    flash[:notice] = params[:notice]
    flash[:warning] = params[:warning]
  end
  
  def pass_cookies
    # @cookies = cookies
  end
  
  def time_offset
     offset = cookies['time_offset'] || (!response.cookies.nil? ? response.cookies['time_offset'] : nil) || (!request.cookies.nil? ? request.cookies['time_offset'] : nil)
     offset.to_i
  rescue
    flash[:notice] = "MOLTEN has been updated. Please login again."
  end
  helper_method :time_offset
  
  def pages_for(size, options = {})
    default_options = {:per_page => AppConstants::SOLUTIONS_PER_PAGE}
    options = default_options.merge options
    pages = Paginator.new self, size, options[:per_page], (params[:page]||1)
    return pages
  end

  # For testing in dev mode
  # def local_request?
#     false
#   end

  # def default_url_options(options)
  #    defaults = {}
  #    if RAILS_ENV == 'production'
  #        defaults[:protocol] = 'https://'
  #        options[:only_path] = false
  #      else
  #        defaults[:protocol] = 'http://'
  #    end
  #    return defaults
  #  end
  
  exception_data :additional_data

  def additional_data
    { :contact => current_contact,
      :case_number => @case_number,
      :time => @time }
  end
  
  # Renders a downtime page if we are within a current downtime. 
  def check_downtime
    if @downtime = SfmoltenPost.check_downtime_interval
      render(:layout => 'blank', :template => 'scheduled_maintenance/show')
      return false
    end
  end

end