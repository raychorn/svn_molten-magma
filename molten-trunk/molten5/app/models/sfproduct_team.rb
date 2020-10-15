class SfproductTeam < ActiveRecord::Base
  #################
  ### Behaviors ###
  #################
  sync :with => Product_Team
  set_primary_key "sf_id"
end
