class Sfcatdata < ActiveRecord::Base
  sync :with => "CategoryData"
  set_primary_key "sf_id"
  #------------------
  # ASSOCIATIONS
  #------------------
  belongs_to :solution, :class_name => 'Sfsolution', :foreign_key => 'related_sobject_id'
  belongs_to :category, :class_name => 'Sfcatnode', :foreign_key => 'category_node_id'
end
