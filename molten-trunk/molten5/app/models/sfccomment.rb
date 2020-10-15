class Sfccomment < ActiveRecord::Base
  sync :with => CaseComment
  set_primary_key "sf_id"
  #------------------
  # ASSOCIATIONS
  #------------------
  belongs_to :created_by, :class_name => "Sfuser", :foreign_key => "created_by_id"
  belongs_to :support_case, :class_name => "Sfcase", :foreign_key => "parent_id"
  # has_many :comments, :class_name => "Sfccomment", :foreign_key => "parent_id"
  
  #------------------
  # CONSTANTS
  #------------------
  COMMENT_BODY_PARSER = /#{AppConstants::COMMENT_CREATOR_DELIMATOR}\s+(.+)\s+((?m:.+))/i
  
  #------------------
  # CALLBACKS
  #------------------
  after_create :send_email_to_owner
  after_save :set_case_last_updated_time
  
  def set_case_last_updated_time
    if support_case and self.synced_record
      logger.info("Setting last update time for case: #{self.synced_record.last_modified_date}")
      support_case.set_update_time!(self.synced_record.last_modified_date) 
    else
      logger.info("Not setting last update time for case")
    end
  end
  
  #------------------
  # INSTANCE METHODS
  #------------------
  
  # Extracted from comment body
  def author_name
    if read_attribute('comment_body') =~ COMMENT_BODY_PARSER
      $1
    elsif created_by and created_by.sfcontact
      created_by.sfcontact.name
    end
  end
  
  # Extract the +created_by+ id from the body. 
  def comment_body
    if read_attribute('comment_body') =~ COMMENT_BODY_PARSER
      $2
    else
      read_attribute('comment_body')
    end
  end
  
  private
  
  # Sends an email to the +Sfcase+ contact as long as the comment creator isn't also the 
  # +Sfcase#contact. AppSetting.config('Send Comment Notifications') must be set to 
  # AppSetting::SEND_COMMENT_NOTIFICATIONS[:send_notification] as well.
  def send_email_to_owner
    return if !self.support_case or self.support_case.contact == self.created_by
    if AppSetting.config('Send Comment Notifications') == AppSetting::SEND_COMMENT_NOTIFICATIONS[:send_notification]
      SfcontactMailer.deliver_owner_notification(self)
    end
  rescue
    logger.info("Error occured creating case comment notification email: #{$!.message}")
  end
end
