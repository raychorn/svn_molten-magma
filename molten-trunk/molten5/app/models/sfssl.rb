class Sfssl < ActiveRecord::Base
  sync :with => SelfServiceUser
  belongs_to :sfcontact, :foreign_key => "contact_id"
  set_primary_key "sf_id"
end
