class Account < ActiveRecord::Base
  establish_connection :development_sf
end
