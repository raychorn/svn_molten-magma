require File.dirname(__FILE__) + '/../test_helper'

class CaseViewSettingTest < Test::Unit::TestCase
  fixtures :case_view_setting, :sfcontact_setting, :sfcontact
  
  def setup
    @derek = sfcontact(:derek)
    @derek.save
  end

  def test_validation
    # failure - no sfcontact_setting provided
    case_view = CaseViewSetting.new
    assert_invalid case_view, :settings

    # success
    case_view.settings = @derek.settings
    assert case_view.valid?
  end
  
  # If a case_view_setting doesn't exist, we create it for the specified 
  # contact_setting and status.
  def test_create
    before = CaseViewSetting.count
    assert_nil CaseViewSetting.find_by_sfcontact_setting_id(@derek.settings.id)
    case_view = @derek.settings.case_view('New')
    assert_equal before +1, CaseViewSetting.count
    assert case_view.is_a?(CaseViewSetting)
  end
  
  def test_collision
    # failure - user can't case view records with the same status
    test_create
    assert_invalid case_view = CaseViewSetting.new(:status => @derek.settings.case_view_settings.last.status,
                                                   :settings => @derek.settings),
                   :status
    
    # success - change the status
    case_view.status = "In Process"
    assert case_view.valid?
  end
end
