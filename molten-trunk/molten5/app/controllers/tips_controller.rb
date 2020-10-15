class TipsController < ApplicationController
  layout nil
  def list
    @tips = SfmoltenPost.tips_for_page(params[:tips_controller], params[:tips_action])
    
    if downtime = SfmoltenPost.check_downtime_announcement
        @tips << downtime
    end
  end
end
