Quand /^je clique sur le lien "([^"]*)"$/ do |arg1|
	if @browser.link(:text => arg1).exists?
		@browser.link(:text => arg1).click
	else
		@browser.link(:id => arg1).click
	end
end

Quand /^je clique sur le bouton "([^"]*)"$/ do |arg1|
	@browser.button(:value => arg1).click
end

Quand /^je navigue vers "([^"]*)"$/ do |arg1|
	@browser.goto(arg1)
end

Alors /^je devrais voir le texte "([^"]*)"$/ do |arg1|
	@browser.wait_until { @browser.text.include? arg1 }
end

Alors /^je devrais voir le texte "([^"]*)" en moins de "([^"]*)" secondes$/ do |arg1, arg2|
	@browser.wait_until(arg2.to_i) { @browser.text.include? arg1 }
end

Quand /^je saisis "([^"]*)" dans le champ "([^"]*)"$/ do |arg1, arg2|
	if @browser.text_field(:id => arg2).exists?
		@browser.text_field(:id => arg2).set(arg1)
	else
		@browser.text_field(:name => arg2).set(arg1)
	end
end

Quand /^je saisis le mot de passe "([^"]*)" dans le champ "([^"]*)"/ do |arg1, arg2|
	if @browser.text_field(:id => arg2).exists?
		@browser.text_field(:id => arg2).set(arg1)
	else
		@browser.text_field(:name => arg2).set(arg1)
	end
end
