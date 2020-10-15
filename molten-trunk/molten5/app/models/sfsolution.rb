class MyAnalyzer < Ferret::Analysis::Analyzer
    def token_stream(field, str)
      return Ferret::Analysis::StemFilter.new(LowerCaseFilter.new(StandardTokenizer.new(str)))
    end
  end


class Sfsolution < ActiveRecord::Base
  #################
  ### Constants ###
  #################
  STATUSES = {:published => 'Published'}
  
  
  #################
  ### Behaviors ###
  #################
  acts_as_viewable
  sync :with => Solution
  # include Searchable
  acts_as_ferret( { :fields =>
   {
      :sf_id              => {},
      :solution_name      => {:boost => 3},
      :solution_number    => {},
      :solution_note      => {},
      :product_name__c    => {},
      :component__c       => {},
      :product_name       => {},
      :status => {},
      :portal_account_name_id__c => {},
      :public => {}
    }, :remote => true } )
  
  set_primary_key 'sf_id' 
  
  delegate :views, :to => :settings
  delegate :updates, :to => :settings
  delegate :total_votes, :to => :rating
  delegate :relevancy, :to => :settings
  
  
  #------------------
  # ASSOCIATIONS
  #------------------
  has_many :comments, :class_name => "Sfccomment", :foreign_key => "parent_id", :dependent => :destroy
  has_many :attachments, :class_name => "Sfattach", :foreign_key => "parent_id", :dependent => :destroy
  has_many :cat_datas, :class_name => "Sfcatdata", :foreign_key => "related_sobject_id"
  has_many :categories, :class_name => "Sfcatnode", :through => :cat_datas
  has_one :settings, :class_name => "SfsolutionSetting", :foreign_key => "sfsolution_id", :dependent => :destroy
  has_one :rating, :dependent => :destroy
  belongs_to :account, :class_name => 'Sfaccount', :foreign_key => "portal_account_name_id__c"
  
  #------------------
  # CALLBACKS
  #------------------
  after_save :initialize_settings
  after_save :initialize_rating
  after_update :increment_update_count
  
  #------------------
  # CLASS METHODS
  #------------------
  
  # This is used to generate SQL conditions that restrict solutions to those that:
  # - are published
  # - in the user's account tree if they are account-specific
  def self.contact_viewing_restrictions(contact)
    ["status = '#{STATUSES[:published]}' AND (portal_account_name_id__c IS NULL OR portal_account_name_id__c IN (?))",contact.account.all_in_tree.map(&:id)]
  end
  
  def self.find_new(contact)
    sols = Sfsolution.find(:all, :order => "last_modified_date DESC", 
                    :conditions => contact_viewing_restrictions(contact),
                    :limit => AppConstants::SOLUTION_HOME_LIMIT)
    sols.reject { |s| !s.viewable? }
  end
  
  # Sets relevancy ratings for each solution. 
  # Can specify an optional hash that is passed to the #find method.
  def self.set_relevancies(options = {})
    find(:all, {:order => "system_modstamp DESC"}.merge(options)).each { |sol| sol.set_relevancy! }
  end
  
  # Searches solutions. 
  # Result options:
  # - :account_specific
  #   :combine - combines account specific into the results
  #   :separate - returns a 2D array with account-specific solutions listed first (default)
  #   :skip - doesn't return any account-specific solutions
  #   :only - returns only account-specific solutions
  def self.full_text_search(q, contact,options,result_options = {})
     return [0,[]] if q.nil? or q==""
     
     result_options = {:account_specific => :separate}.merge(result_options)
     
     default_options = {:limit => AppConstants::SOLUTIONS_PER_PAGE, :page => 1,
                        :limit_specific => AppConstants::SOLUTIONS_PER_PAGE, :page_specific => 1}
     options = default_options.merge options
     
     # require that solutions be published
     q += " +status:#{STATUSES[:published]}"
     
     # require that solutions be public
     q += " +public:true"
     
     # non-account specific solutions
     total, solutions = if [:combine, :separate, :skip].include?(result_options[:account_specific])
       # get the offset based on what page we're on
       options[:offset] = options[:limit] * (options.delete(:page).to_i-1)
       
       # don't want any solutions that specify an account
       specific_q = q + " +portal_account_name_id__c:'' "
       
       results = find_by_contents(specific_q, options)
       size = results.size
       filtered_results = results.reject { |r| !r.portal_account_name_id__c.blank? }
       removed_results = size - filtered_results.size
       [(results.total_hits - size), filtered_results]
     else
       [0,[]]
     end
     
     # account specific solutions
     total_specific, solutions_specific = if [:combine, :separate, :only].include?(result_options[:account_specific])
        # get the offset based on what page we're on
        options[:offset_specific] = options[:limit_specific] * (options.delete(:page_specific).to_i-1)

        # limit solutions to the +contact's+ account
        specific_q = q + " +portal_account_name_id__c:("
        # account_list = contact.account_list.map { |a| " OR " + "portal_account_name_id__c:" + a.id }.join(' ')
        account_list = contact.account.all_in_tree.map do |a| 
           a.id 
        end.join(' OR ')
        specific_q += account_list + ') '
        results = find_by_contents(specific_q, options)
        
        [results.total_hits, results]
     else
      [0,[]]
     end
     
     
     
     case result_options[:account_specific]
     when :combine
       [total+total_specific,solutions_specific+solutions]
     when :separate
       [total_specific,solutions_specific,total,solutions]
     when :skip
       [0,[],total,solutions]
     when :only
       [total_specific,solutions_specific,0,[]]
     end
  end
  
  # Find the popular solutions since options[:range] ago (pass in a Time object, ie - 5.hours.ago). 
  # Default is AppConstants::MOST_POPULAR_LAST_N_DAYS.days.ago
  # Returns a 2D array of Solutions and the number of times that solution was viewed. 
  def self.find_popular_in_range(contact,options = {})
    options = {:range => AppConstants::MOST_POPULAR_LAST_N_DAYS, 
               :limit => 100}.merge(options)
    results = Sfsolution.find_by_sql "SELECT viewable_id, count(*) views FROM viewing where viewable_type='Sfsolution' and DATE_SUB(CURDATE(),INTERVAL #{options[:range]} DAY) <= created_at group by viewable_id order by views DESC limit #{options[:limit]}"
    results.map! { |r| [Sfsolution.find_by_sf_id(r.viewable_id), r.attributes["views"].to_i]}
    results.reject! { |r| r.first.nil? or (!r.first.portal_account_name_id__c.nil? and !contact.account.all_in_tree.map(&:id).include?(r.first.portal_account_name_id__c))}
    results.reject { |r| !r.first.viewable? }.slice(0..AppConstants::MOST_POPULAR_LIMIT)
  end

  # Find number of new solutions created in last options[:range] days.
  # Default is AppConstants::NEW_SOLUTIONS_LAST_N_DAYS
  # Returns number
  def self.new_solutions_in_range(contact,options = {})
    options = {:range => AppConstants::NEW_SOLUTIONS_LAST_N_DAYS}.merge(options)
    results = Sfsolution.find_by_sql "SELECT * FROM sfsolution s where DATE_SUB(CURDATE(),INTERVAL #{options[:range]} DAY) <= last_modified_date and status = '#{STATUSES[:published]}' AND (portal_account_name_id__c IS NULL OR portal_account_name_id__c IN (#{contact.account_list.map(&:id).map { |id| "'" + id + "'"}})) order by last_modified_date DESC;"    # disable after 6/9/2007
    results.reject! { |r| !r.viewable? or (!r.portal_account_name_id__c.nil? and !contact.account.all_in_tree.map(&:id).include?(r.portal_account_name_id__c)) }
    return [results.size, results]
  end
  
  
  def self.number_new_solutions_in_range(contact,options = {})
    @total, @results = Sfsolution.new_solutions_in_range(contact,options)
    return @total
  end

  #------------------
  # INSTANCE METHODS
  #------------------
  
  # Returns true if this solution's categories or category ancestors includes the root node. 
  def public?
    category_tree.include?(Sfcatnode.root)
  end
  alias public public?
  
  def viewable?
   published? and public?
  end
  
  # Sets and saves the relevancy rating for the solution. 
  # Takes the following into account:
  #   - the ratings
  #   - the # of views
  #   - The # of times the solution has been updated.
  def set_relevancy!
    # calculate total of ratings
    ratings = rating.count_attributes
    ratings.each do |key,value|
      ratings[key] = value * SolutionRelevancy.send("rating_value_#{key}")
    end
    total = ratings.values.inject(0) { |sum, count| sum + count }
    
    # calculate total of views
    total += views * SolutionRelevancy.view_value
    
    # calculate updates
    total += updates * SolutionRelevancy.update_value
    
    # total # of items that are included in the updates
    num_of_items = total_votes + views + updates

    # set the relevancy
    settings.update_attribute('relevancy',num_of_items > 0 ? total/num_of_items : AppConstants::DEFAULT_SOLUTION_RELEVANCY)   
  end
  
  # Increments the specified rating level and saves the rating.
  def rate!(level)
    rating.increment!(level)
  end
  
  # True if votes have been placed.
  def any_votes?
    total_votes > 0
  end
  
  # Returns a 2-D Array with:
  #   - The friendly name of the rating
  #   - The actual attribute name
  #   - The number of votes.
  def list_ratings
    final_result = []
    # grab all of the rating attributes and counts and turn them into an array
    rating_results = rating.count_attributes.to_a
    
    # order the rating counts and attributes
    ordered_results = []
    ['one', 'two', 'three', 'four'].each do |order|
      rating_results.each do |result|
        if order == result[0]
          ordered_results << result
        end
      end
    end
    
    # add in the friendly name
    for i in 0...ordered_results.length
      final_result << [AppConstants::FRIENDLY_RATING_NAMES[i],ordered_results[i][0],(ordered_results[i][1].to_f/total_votes.to_f)*100]
    end
    
    final_result
  end
  
  # Returns an array of +Sfnodes+ with all of the categories that the solution belongs to, including
  # its ancestors.
  def category_tree
    cats = []
    categories.each do |cat|
      cats << cat
      cats = cats + cat.ancestors
    end
    return cats
  end
  
  def name
    solution_name
  end
  
  def note
    solution_note
  end
  
  def published?
    status == STATUSES[:published]
  end
  
  def publish!
    update_attribute('status',STATUSES[:published])
  end
  
  private
  
  # create local settings unless it already exists.
  def initialize_settings
    create_settings if self.sf_id =~ /\D/ and settings.nil?
  end
  
  # creates rating unless it already exists.
  def initialize_rating
    create_rating if self.sf_id =~ /\D/ and rating.nil?
  end
  
  # increments the # of times the solution has been updated after being saved
  def increment_update_count
    self.settings.increment!(:updates) if settings
  end
end
