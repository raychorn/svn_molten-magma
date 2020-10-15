class Attachment < SalesforceRecord
  # cloned_class :sfattach
  set_primary_key "id"
  
  validates_presence_of :body, :body_length, :is_private, :name, :parent_id, 
                        :if => Proc.new { |attachment| !attachment.validate_attributes }
  
  #------------------
   # VIRTUAL ATTRIBUTES
   #------------------
   attr_accessor :validate_attributes
end
