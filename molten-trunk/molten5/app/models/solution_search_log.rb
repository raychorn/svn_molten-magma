class SolutionSearchLog < ActiveRecord::Base
  set_primary_key 'id'
  #------------------
  # ASSOCIATIONS
  #------------------
  belongs_to :contact, :class_name => "Sfcontact", :foreign_key => "contact_id"
  
  #------------------
  # VALIDATIONS
  #------------------
  validates_presence_of :contact, :results_count, :term
end
