class CaseComment < SalesforceRecord  
  #------------------
  # ASSOCIATIONS
  #------------------
  belongs_to :created_by, :class_name => "Sfcontact", :foreign_key => "created_by_id"
  belongs_to :support_case, :class_name => "Sfcase", :foreign_key => "parent_id"
  
  #------------------
  # CONSTANTS
  #------------------
  COMMENT_CREATOR_IDENTIFIER = /#{AppConstants::COMMENT_CREATOR_DELIMATOR}\w+\n/
  
  #------------------
  # CALLBACKS
  #------------------
  before_validation_on_create :add_creator_identifier_to_body
  after_create :update_case

  #------------------
  # INSTANCE METHODS
  #------------------
  
  # Prepend the creator id to the comment body.
  def add_creator_identifier_to_body
    
    return if self.comment_body.nil? or (self.comment_body =~ COMMENT_CREATOR_IDENTIFIER) or self.created_by_id.nil?
    write_attribute('comment_body',
                     self.comment_body.insert(0, "#{AppConstants::COMMENT_CREATOR_DELIMATOR} #{created_by.name}\n")
                    )
  end
  
  # Updates the +last_modified_date+ attribute of the associated case. 
  def update_case
    return unless parent and parent.clone_exists?
    parent.last_modified_date = Time.now.gmtime-(11*60*60*60)
    parent.save_and_update
  rescue
  end
  
  
end
