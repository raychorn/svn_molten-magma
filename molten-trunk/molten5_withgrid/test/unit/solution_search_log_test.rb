require File.dirname(__FILE__) + '/../test_helper'

class SolutionSearchLogTest < Test::Unit::TestCase
  fixtures :solution_search_log, :sfcontact

  def test_validation
    # failure - creator, term, and result count not provided
    log = SolutionSearchLog.new
    assert_invalid log, :contact, :term, :results_count
    
    # success
    log.contact = Sfcontact.find(:first)
    log.term = "the term"
    log.results_count = 12
    
    assert_valid log
  end
end
