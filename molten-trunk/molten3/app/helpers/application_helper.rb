# Methods added to this helper will be available to all templates in the application.
module ApplicationHelper

def acctEntity
    @desc=Account.connection.get_entity_def("Account")
    @nm=@desc.columns
    @nm.each do |val|
      @api=val.api_name
    end
    return @nm
  end
end
