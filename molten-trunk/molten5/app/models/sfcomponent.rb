class Sfcomponent < ActiveRecord::Base
  #------------------
  # BEHAVIORS
  #------------------
  sync :with => Component
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

end
