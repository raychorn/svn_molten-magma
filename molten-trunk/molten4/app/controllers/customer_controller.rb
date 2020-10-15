class CustomerController < ApplicationController


	def list
	      #@recipes = Customer.find_all
          @msg1="ttttt"
	      table_name="Customer"
	      #@recipes = eval("#{table_name}").find_all
	      @recipes = Customer.find_all
	      @sf_id="112125"
	      @recipes1=eval("#{table_name}").find(:first, :conditions => "id = '#{@sf_id}'")
	      if (@recipes1)
	       @msg="records count is 1"
	      end
	      
	end
	
	def add
	 tempHash = Hash.new()
	 tempHash["name"]="ash"
	 tempHash["type"]="ttttt"
	 sacct=Customer.new(tempHash)
     sacct.save
     puts sacct.id
	end
	
	def new
	   @rec=Customer.new
	   @exist=Customer.find_all
	end
	
	def create
      @recipe = Customer.new(@params['customer'])
      @recipe.cdate = Date.today
      if @recipe.save
          redirect_to :action => 'list'
      else
          render_action 'new'
    end
    
    def edit
      @cust = Customer.find(params[:id])
    end

    def update
      @cust = Customer.find(params[:id])
      if @cust.update_attributes(params[:customer])
        flash[:notice] = 'Customer records was successfully updated.'
        redirect_to :action => 'list'
      else
        render :action => 'edit'
      end
    end
    
    def view
      @msg="valid string"
      #@attr=@params["id"]
      #@custid=Customer.find(@params['id'])
      
      #@custid=Customer.find(params[:id])
      #puts "testttttt"
      #puts @custid
      #
      @table_name="Customer"
      @usr = Users.find_all 
      puts "MESSAGE IS #{@usr}"   
      print "MESSAGE IS #{@usr}"   
    end
    
    def test
      render_text "ttttt"
      @msg1="ttttt"
      print "test"
    end
  
end
end
