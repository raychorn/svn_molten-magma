class Sfgroup < ActiveRecord::Base
  #------------------
  # BEHAVIORS
  #------------------
  sync :with => Group
  set_primary_key "sf_id"

  #------------------
  # CONSTANTS
  #------------------

  #------------------
  # CLASS METHODS
  #------------------

  ########################
  ### Instance Methods ###
  ########################
  
  def to_s
    name
  end
  alias sort_name to_s
end