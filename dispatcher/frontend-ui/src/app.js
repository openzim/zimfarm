try { var zimfarm_webapi = environ.ZIMFARM_WEBAPI; } catch { var zimfarm_webapi = "https://api.farm.openzim.org"; }


var app = new Vue({
	el: "#app",
	data: {
		api_url: zimfarm_webapi,
		loading: false,
		schedules: [],
		languages: [],
		tags: [],
		selectedLanguages: "",
		selectedTags: "",
		selectedCategories: "",
		categories: ["gutenberg", "other", "phet", "psiram", "stack_exchange", "ted", "vikidia", "wikibooks", "wikinews", "wikipedia", "wikiquote", "wikisource", "wikispecies", "wikiversity", "wikivoyage", "wiktionary"],
	},
	methods: {
		loadMetaData: function () {
			// download languages
			let parent = this;
			this.loading = true;
			axios.get(zimfarm_webapi + '/languages/', {params: {limit: 1000}})
		    .then(function (response) {
			    for (var i=0; i<response.data.items.length; i++){
			    	parent.languages.push(response.data.items[i]);
			    }
	        })
			.catch(function (error) {
			    console.log(error);
			})
			.then(function () {
			    parent.loading = false;
			});

			// download tags
			this.loading = true;
			axios.get(zimfarm_webapi + '/tags/', {params: {limit: 1000}})
		    .then(function (response) {
			    for (var i=0; i<response.data.items.length; i++){
			    	parent.tags.push(response.data.items[i]);
			    }
	        })
			.catch(function (error) {
			    console.log(error);
			})
			.then(function () {
			    parent.loading = false;
			});
		},
		loadSchedules: function () {
			let parent = this;
			this.loading = true;
			var params = {limit: 2000};
			if (this.selectedLanguages) {
				params.lang = this.selectedLanguages;
			}
			if (this.selectedTags) {
				params.tag = this.selectedTags;
			}
			if (this.selectedCategories) {
				params.category = this.selectedCategories;
			}
			axios.get(zimfarm_webapi + '/schedules/', {params: params})
		    .then(function (response) {
		    	parent.schedules = [];
			    for (var i=0; i<response.data.items.length; i++){
			    	var schedule = response.data.items[i];
			    	if (schedule["most_recent_task"]) {
			    		schedule["most_recent_task"]["on"] = moment(schedule["most_recent_task"]["updated_at"]).fromNow()
			    	}
			    	parent.schedules.push(schedule);
			    }
	        })
			.catch(function (error) {
			    console.log(error);
			})
			.then(function () {
			    parent.loading = false;
			});
		},
 		
	},
	beforeMount(){
		this.loadMetaData();
		this.loadSchedules();
	},
})
