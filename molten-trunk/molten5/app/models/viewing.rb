class Viewing < ActiveRecord::Base
  include Cachable
  set_primary_key "id"
  
  #------------------
  # ASSOCIATIONS
  #------------------
  belongs_to :viewable, :polymorphic => true
  belongs_to :sfcontact
  
  #------------------
  # VALIDATIONS
  #------------------
  validates_presence_of :viewable, :sfcontact
  
  #------------------
  # CALLBACKS
  #------------------
  
  # after_create :expire
  
  def expire
    expire_cache(self)
  end
end
