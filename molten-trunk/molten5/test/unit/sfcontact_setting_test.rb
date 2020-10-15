require File.dirname(__FILE__) + '/../test_helper'

class SfcontactSettingTest < Test::Unit::TestCase
  fixtures :sfcontact_setting, :sfcontact
  
  def setup
    @contact = sfcontact(:derek)
    SfcontactSetting.delete_all
  end

  def test_validation
    # failure - no sfcontact specified
    setting = SfcontactSetting.new
    assert_invalid setting, :sfcontact
    
    # success
    setting.sfcontact = @contact
    assert setting.valid?
  end
  
  # if a sfcontact doesn't have an sfcontact_setting record yet, 
  # we create it the first time the method is called.
  def test_create
    assert_nil SfcontactSetting.find_by_sfcontact_id(@contact.id)
    assert @contact.save 
    assert SfcontactSetting.find_by_sfcontact_id(@contact.id)
    assert @contact.settings
  end
end
