require File.dirname(__FILE__) + '/../test_helper'

class ViewingTest < Test::Unit::TestCase
  fixtures :viewing, :sfcontact, :sfsolution

  def test_validation
    # failure - req'd attributes not provided
    viewing = Viewing.new
    assert_invalid viewing, :viewable, :sfcontact
    
    viewing.viewable = Sfsolution.find(:first)
    viewing.sfcontact = Sfcontact.find(:first)
    assert viewing.valid?
  end
end
