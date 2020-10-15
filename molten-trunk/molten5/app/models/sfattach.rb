class Sfattach < ActiveRecord::Base
  sync :with => Attachment
  set_primary_key "sf_id"
  # Number of attachments to the custom homepage to show
  PER_PAGE = 20
  
  ###################
  ### Assocations ###
  ###################
  belongs_to :last_modified_by, :class_name => "Sfuser", :foreign_key => "last_modified_by_id"
  # belongs_to :solution, :class_name => "Sfsolution", :foreign_key => "parent_id"
  
  #################
  ### Callbacks ###
  #################
  after_save :set_case_last_updated_time
  
  def set_case_last_updated_time
    parent.set_update_time!(self.last_modified_date) if parent.is_a?(Sfcase)
  end
  
  #####################
  ### Class Methods ###
  #####################
  
  # Searches for attachments to the given +attachable+. 
  def self.search(attachable,term,options = {})
    term = "%#{term}%"
    sort = options[:sort] || 'sfattach.created_date'
    order = options[:order] || 'ASC'
    page = options[:page] || 1
    paginate(:page => page, :per_page => PER_PAGE,
             :conditions => ["parent_id = ? AND (sfattach.name LIKE ? OR sfuser.first_name LIKE ? OR sfuser.last_name LIKE ?)",
                                attachable.id,term,term,term],
               :include => [:last_modified_by],
               :order => "#{sort} #{order}")
  end
  
  ########################
  ### Instance Methods ###
  ########################
  
  # Returns the file extension based on the +name+.
  def extension
    name.gsub(/\w+\./,'')
  end
  
  # Parent can be a solution or a case
  def parent
    if record = Sfsolution.find_by_sf_id(parent_id)
      record
    else
      record = Sfcase.find_by_sf_id(parent_id)
    end
  end
end
