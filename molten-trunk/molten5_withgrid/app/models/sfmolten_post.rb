class SfmoltenPost < ActiveRecord::Base
  #------------------
  # BEHAVIORS
  #------------------
  sync :with => MoltenPost
  set_primary_key "sf_id"
  
  #------------------
  # CONSTANTS
  #------------------
  ARTICLE_TYPE   = '012300000000m8HAAQ'.freeze  
  
  TIP_TYPE       = '012300000000m8IAAQ'.freeze
  
  DOWNTIME_TYPE  = '01230000000DSOaAAO'.freeze
  
  # not sure if AAQ is right...might be AAO...need to check
  MARKETING_TYPE = '012300000001ZjzAAE'.freeze
  
  #------------------
  # CLASS METHODS
  #------------------
  
  # Finds all articles with the most recently created article first. 
  def self.find_articles(options = {})
    options = {:conditions => ["record_type_id = ?", ARTICLE_TYPE], :order => "created_date DESC"}.merge(options)
    find(:all, options)
  end
  
  # Finds a single article
  def self.find_article(id)
    options = {:conditions => ["record_type_id = ? and sf_id = ?", ARTICLE_TYPE, id] }
    find(:first,options)
  end
  
  # Finds all tips for the specified +controller+ and +action+. 
  # Grabs tips that directly match this controller/action.
  #
  # If the 'application' controller is specified, the tip will appear throughout the site.
  def self.tips_for_page(controller,action)
    # for a specific controller action
    tips = find(:all, :conditions => ["record_type_id = ? and page__c = ?", TIP_TYPE, "#{controller}/#{action}"])
    # for the entire application
    tips = tips + find(:all, :conditions => ["record_type_id = ? and page__c = ?", TIP_TYPE, 'application'])
  end
  
  # Checks if NOW is inside downtime interval. Only one (last entered) downtime event is returned.
  # Used during downtime to inform user and to limit functionality.
  def self.check_downtime_interval(options = {})
#    now = Time.now.strftime("%Y-%m-%d %H:%M:%S")
    now = Time.now.to_s(:db)
    options = {:conditions => ["record_type_id = ? and valid_from__c < ? and valid_to__c > ?",  DOWNTIME_TYPE, now, now], :order => "created_date DESC"}.merge!(options)
    find(:first, options)
  end

  # Checks if NOW is before downtime interval. Only one (last entered) downtime event is returned.
  # Used to display downtime announcement.
  def self.check_downtime_announcement(options = {})
    early = 7.days.from_now.strftime("%Y-%m-%d %H:%M:%S") # announce 1 week ahead of event
    now = Time.now.strftime("%Y-%m-%d %H:%M:%S")
    options = {:conditions => ["record_type_id = ? and valid_from__c < ? and valid_from__c > ?",  DOWNTIME_TYPE, early, now], :order => "created_date DESC"}.merge!(options)
    find(:first, options)
  end
  
  # Finds the most recent marketing message
  def self.check_marketing_message(options = {})
    cur_time = Time.now.utc # + Time.now.gmt_offset
    now = cur_time.strftime("%Y-%m-%d %H:%M:%S")
    options = {:conditions => ["record_type_id = ? and valid_from__c <= ?",  MARKETING_TYPE, now], 
               :order => "created_date DESC"}.merge!(options)
    find(:first, options)
  end
  
  # Returns the most recent marketing message if the +contact+ hasn't viewed it yet.
  # The marketing message is displayed 3 times.
  def self.check_marketing_message_for_contact(contact)
    message = check_marketing_message
    if message
      if contact.last_read_marketing_message != message
        contact.update_attribute(:marketing_message_read_count,0)
        contact.update_attribute(:last_read_marketing_message,message)
        message
      elsif contact.marketing_message_read_count < 2
        contact.increment!(:marketing_message_read_count)
        message
      else
        nil
      end
    else
      nil
    end
  end
  
  ########################
  ### Instance Methods ###
  ########################
 
  def title
    if !title_long__c.blank?
      title_long__c
    else
      name
    end
  end
end
