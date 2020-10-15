class CaseReport < ActiveRecord::Base
  #################
  ### Behaviors ###
  #################
  set_primary_key 'id'
  serialize :status_array
  serialize :column_array
  serialize :account_ids_array
  
  ####################
  ### Associations ###
  ####################
  belongs_to :contact, :class_name => 'Sfcontact'
  before_save :stringify_query
  
  #################
  ### Constants ###
  #################
  NON_QUERY_KEYS = [nil, "\n", "", "controller", "action", "commit", "id", "status"]
  
  ########################
  ### Instance Methods ###
  ########################
  def cases
    raise NotImplemented
  end
  
  def to_options
    self.class.to_options(query)
  end
  
  def account_array
    if account_ids_array.is_a?(Array) and account_ids_array.any?
      Sfaccount.find(account_ids_array)
    else
      [contact.company] + contact.company.children
    end
  end
  
  # Used to determine if the given +contact+ can modify this report.
  def editable?(contact)
    if contact_id == contact.id
      true
    else
      logger.info "contact [#{contact.id}] isn't the contact for this case report #{contact_id}"
      false
    end
  end
  
  # Used to determine if the given +contact+ can view this report.
  def readable?(contact)
    account_id == contact.account_id
  end
  
  def cols
    list_cols = Array.new
    column_array.each do |c|
      name = c.sub(/[a-z]+\_/,'')
      list_cols << {
       :attr => c, 
       :sort => name.gsub('___','.'),
       :desc => CaseColumnsSetting::YOUR_CASE_COLUMNS.find { |s| s[:col] == name}[:desc],
       :meth => CaseColumnsSetting::YOUR_CASE_COLUMNS.find { |s| s[:col] == name}[:meth],
       }
    end
    list_cols
  end
  
  def all?
    to_options["all"]
  end
  
  class << self
    
    # The default report (for all accounts and contacts)
    def all_cases(options = {})
      report = self.new
      report.query = self.to_query_string({:sort => 'sfcase.last_modified_date', :order => 'DESC'}.merge(options))
      report.contact_id = current_contact.id
      report.account_id = current_contact.account.id
      report.shared = false
      report
    end
    
    # Takes a hash and finds the matching saved report if it exists.
    # 
    # Examples
    # 
    #   CaseReport.match_existing({"baz"=>"bing"}) #=> nil
    #   CaseReport.match_existing({"foo"=>"bar"}) #=> #<CaseReport>
    # 
    # Returns <tt>nil</tt> if no matching saved report was found, otherwise
    # it returns the instance of the matching case report.
    # 
    def match_existing(contact_id, query)
      query = self.to_options(query)
      
      if reports = self.find(:all, :conditions => ["contact_id = ?", contact_id], :readonly => true, :select => 'id, query')
        reports.each do |report|
          return self.find(report.id) if report.to_options == query.reject { |k, v| NON_QUERY_KEYS.include?(k) }
        end
        return nil
      end
    end
    
    # Takes a string like <tt>"foo=bar&baz=bing"</tt> and produces
    # <tt>{"baz"=>"bing", "foo"=>"bar"}</tt>.
    # 
    # Operates on the <tt>query</tt> property to allow for merging options.
    # 
    # Examples
    # 
    #   case_report.query = "foo=bar&baz=bing"
    #   case_report.to_options #=> {"baz"=>"bing", "foo"=>"bar"}
    # 
    # Returns the <tt>query</tt> string as a bonafide hash.
    # 
    def to_options(query)
      return query if query.is_a?(Hash)
      # some key parts stolen from CGI.parse
      query.
      split(/[&;]/n).inject({}) do |params, entry|
        key, value = entry.split('=',2).map{|s| CGI.unescape(s)}
        # treat arrays specially
        if key && key.from(-2).to(-1) == "[]"
          key = key.to(-3) # get rid of the "[]"
          params[key] ||= []
          params[key] << value
          params
        else
          params.merge(key => value)
        end
      end.
      # reject nil => nil entries that exist with &s at the end or beginning
      reject { |k, v| NON_QUERY_KEYS.include?(k) }
    end
    
    # Takes a hash and converts it to an equivalent query string for storage.
    # 
    # Examples
    # 
    #   case_report.query = {"baz"=>"bing", "foo"=>"bar"}
    #   case_report.to_query_string #=> "foo=bar&baz=bing"
    # 
    # Returns the <tt>query</tt> hash as a string.
    # If <tt>query</tt> is already a string, it returns <tt>query</tt>.
    # 
    def to_query_string(query)
      logger.info "query string: #{query}"
      return query if query.is_a?(String)
      
      query_string = Array.new
      
      query.each do |key,value|
        logger.info "key: #{key}"
        logger.info "value: #{value}"
        next if NON_QUERY_KEYS.include?(key)
        if value.is_a?(Array)
          value.each do |v|
            query_string << "#{CGI.escape(key)}[]=#{CGI.escape(v)}"
          end
          query_string
        else
          query_string << "#{CGI.escape(key)}=#{CGI.escape(value)}"
        end
      end
      return query_string.join('&')
      # The code below doesn't appear to handle all of the params 
      # the query param '&' logis is off (plus I think)
      # query.inject("") do |query_string, (key, value)|
      #        logger.info "key: #{key}"
      #        logger.info "value: #{value}"
      #        return query_string if NON_QUERY_KEYS.include?(key)
      #        if value.is_a?(Array)
      #          value.each do |v|
      #            query_string << "&#{CGI.escape(key)}[]=#{CGI.escape(v)}&"
      #          end
      #          query_string
      #        else
      #          query_string << "&#{CGI.escape(key)}=#{CGI.escape(value)}&"
      #        end
      #      end
    end
    
  end
  
  private
  
  # Ensure the query is saved as a query string.
  def stringify_query
    self.query = self.class.to_query_string(self.query)
  end
  
end
