class CategoryData < ActiveRecord::Base
  establish_connection :development_sf
  set_table_name "category_data"  
end
