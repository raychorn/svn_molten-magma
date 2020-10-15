class Admin::BaseController < AbstractAdminController
  def expire_fragments
    expire_fragment(%r{.})
    render(:text => "Cached Fragments Deleted.")
  end
end
