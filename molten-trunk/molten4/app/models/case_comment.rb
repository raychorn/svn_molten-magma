class CaseComment < ActiveRecord::Base
  establish_connection :development_sf
  #establish_connection(:adapter => 'activesalesforce', :username => "sfbatch@molten-magma.com", :password => "sf@magma05", :url => "https://www.salesforce.com/services/Soap/u/7.0")	
  #establish_connection(:adapter => 'activesalesforce', :username => "sf_molten_generic_chipwrights@molten-magma.com", :password => "wright", :url => "https://www.salesforce.com/services/Soap/u/7.0")	
        
end
