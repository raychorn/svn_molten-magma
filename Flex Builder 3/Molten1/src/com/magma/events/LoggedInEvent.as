package com.magma.events {
	import com.salesforce.results.LoginResult;
	
	import flash.events.Event;
	
	public class LoggedInEvent extends Event {
        public function LoggedInEvent(type:String, lr:LoginResult) {
            super(type);
    
            this.loginResult = lr;
        }

        public static const LOGGED_IN:String = "loggedInEvent";

		public var loginResult:LoginResult;
		
        override public function clone():Event {
            return new LoggedInEvent(type, loginResult);
        }
	}
}