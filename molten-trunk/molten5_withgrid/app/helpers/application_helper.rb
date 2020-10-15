# Methods added to this helper will be available to all templates in the application.
module ApplicationHelper
  include AuthenticationSystem
  include SalesforceHelper
  
  def nav_class(controller_name)
    if controller_name =~ /#{params[:controller]}/ then "selected" end
  end
  
  # Returns true if the controller is a subclass of AbstractBeastController. 
  def in_beast?
    controller.is_a?(AbstractBeastController)
  end
  
  # 
  # Given some amount of _seconds_, returns a pretty String of the form:
  # 
  #   Int (Years | Weeks | Days | Hours | Minutes | Seconds)
  # 
  def clean_age( seconds, options = {} )
    options = {:utc => false}.merge(options)
    return if seconds.nil?
    seconds = (Time.now - (options[:utc] ? seconds - (60*60*7) : seconds) ).to_i
  
    count, units = if (yrs = seconds / 60 / 60 / 24 / 7 / 52) > 0
      [yrs, "Year"]
    elsif (wks = seconds / 60 / 60 / 24 / 7) > 0
      [wks, "Week"]
    elsif (days = seconds / 60 / 60 / 24) > 0
      [days, "Day"]
    elsif (hrs = seconds / 60 / 60) > 0
      [hrs, "Hour"]
    elsif (min = seconds / 60) > 0
      [min, "Minute"]
    else
      [seconds, "Second"]
    end
  
    "#{count} #{count != 1 ? units.pluralize : units}"
  end
  
  # This is weird...it's grabing the record
  def formatted_date(date = nil)
    return '' unless date
    date.last_modified_date.strftime("%m/%d/%y")
  end
  
  def format_time(time)
#    time.strftime("%m/%d/%y") if !time.blank?
    time.strftime("%d-%b-%Y %H:%M:%S") if !time.blank?
  end
  
  def ajax_indicator(id = "indicator")
    <<-END
    <div style="display:none" id='#{id}'>
		  #{image_tag('indicator_arrows_circle.gif')}
		</div>
		END
  end
  
  # 
  # Creates links to available pages.  
  # Accepts an options hash with the following options:
  #   - kind: If provided, the total count of object is provided.
  #   - pages: The Page object to apply pages to. Defaults to +@pages+.
  #   - params: merges these with the existing params
  def pages( options = {} )
    options = {:kind => nil, :pages => @pages, :params => {}}.merge(options)
    if options[:pages] and options[:pages].page_count > 1
      html = <<-END
        <div class="pages">
          Page: #{pagination_links(options[:pages], {:window_size => 6, :params => params.merge(options[:params]).reject { |key,value| key == 'controller' }}).sub(/\d+(?=\s|$)/, '<span class="this_page">\&</span>').sub("...", '<span class="break">...</span>')}
          #{options[:kind].nil? ? "" : "(#{options[:pages].last_page.last_item} #{options[:kind]})"}
        </div>
      END
    end
  end
  
  # Takes a +Time+ object and converts it to the user's time using
  # their +time_offset+. 
  def contact_time(time)
    return '' if !time.is_a?(Time) and !(Float Integer).include?(time_offset.class)
    time - time_offset
  rescue
    time
  end
  alias :ct :contact_time
  
  def link_to_faq(name = 'FAQ')
    link_to name, '/FAQ.html', :popup => ['Molten FAQ', 'height=500,width=700']
  end
  
  # This method builds an image path based on a file +kind+.  If a +kind+ is not
  # recognized +default+ is used instead.  +path_prefix+ is prepended to the
  # path before it is returned.
  def file_kind_image_path( path_prefix, kind, default = "file.gif" )
    if File.exist? File.join( RAILS_ROOT, "public", "images",
                              path_prefix, kind.downcase + ".gif" )
      File.join(path_prefix, kind.downcase + ".gif")
    else
      File.join(path_prefix, default)
    end
  end
  
  def file_download_link
    return '#' unless !cookies[:LAVA_Token].blank?
    "https://magma.subscribenet.com/control/lava/login?LAVA_User=#{current_contact.email}&LAVA_Token=#{cookies[:LAVA_Token]}&action=authenticate&nextURL=purchases"
  end
end

