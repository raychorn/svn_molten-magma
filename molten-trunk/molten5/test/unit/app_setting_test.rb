require File.dirname(__FILE__) + '/../test_helper'

class AppSettingTest < Test::Unit::TestCase
  fixtures :app_setting
  
  def test_validation
    setting = AppSetting.new
    # failure - req'd attributes not provided
    assert_invalid setting, :name, :value
    
    # success
    setting.name = "bannanas"
    setting.value = "12"
    assert_valid setting
  end

  def test_config
    assert_equal app_setting(:salesforce_form_submission).value, AppSetting.config("Salesforce Form Submissions")
  end
  
end
