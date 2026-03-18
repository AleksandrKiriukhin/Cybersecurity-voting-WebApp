<reference types="cypress" />

describe('E2E Admin Flow: Tworzenie nowego głosowania', () => {
    
    const adminEmail = 'admin@ubb.edu.pl';
    const adminPassword = '12345678Aa@';
    const votingName = 'Głosowanie Testowe E2E ' + Date.now();
    const departmentId = '1'; 
    
    const today = new Date();
    const startDate = today.toISOString().split('T')[0];
    
    const nextWeek = new Date();
    nextWeek.setDate(today.getDate() + 7);
    const endDate = nextWeek.toISOString().split('T')[0];
    
    const maxVotes = '3';

    const candidates = [
        { firstName: 'Adam', lastName: 'Nowak'},
        { firstName: 'Ewa', lastName: 'Kowalska'},
        { firstName: 'Jan', lastName: 'Zieliński' },
    ];
    
    before(() => {
        cy.log('Krok 0: Logowanie administratora');
        cy.visit('/login');

        // cy.get('input[name="email"]').type(adminEmail);
        // cy.get('input[name="password"]').type(adminPassword);
        // cy.get('button[type="submit"]').click();
        
        // cy.url().should('not.include', '/login');
    });

    it('Powinien przejść przez nawigację admina, utworzyć nowe głosowanie i sprawdzić przekierowanie', () => {
        let createdVotingId;

        const TEST_RECAPTCHA_TOKEN = 'test-token-always-success'; 
        
        cy.get('textarea[name="g-recaptcha-response"]', { timeout: 10000 })
          .should('exist') 
          .invoke('val', TEST_RECAPTCHA_TOKEN);
          
        cy.get('input[name="email"]').type(adminEmail);
        cy.get('input[name="password"]').type(adminPassword);
        
        cy.get('button[type="submit"]').click();

        cy.log('Krok 1: Przejście do /user-info');
        cy.visit('/user-info');
        cy.url().should('include', '/user-info');

        cy.log('Krok 2: Przejście do Moje głosowania');
        cy.get('a:contains("Moje głosowania")').should('be.visible').click();
        cy.url().should('include', '/user-votings');

        cy.log('Krok 3: Przejście do /create-voting');
        cy.get('a:contains("Nowe głosowanie")').should('be.visible').click();
        cy.url().should('include', '/create-voting');

        cy.log('Krok 4: Wypełnianie danych głosowania');
        cy.get('input[name="name"]').type(votingName);
        cy.get('#department_id').select(departmentId); 
        cy.get('input[name="start_date"]').type(startDate);
        cy.get('input[name="end_date"]').type(endDate);
        cy.get('input[name="max_votes_per_person"]').type(maxVotes);

        cy.log('Krok 5: Dodawanie i wypełnianie pól kandydatów');
        
        candidates.forEach((candidate, index) => {
            
            if (index > 0) {
                 cy.get('button:contains("Dodaj kandydata")').click(); 
            }

            cy.get(`#candidate-first-name-${index}`).type(candidate.firstName); // Wymaga selektorów z indeksem
            cy.get(`#candidate-last-name-${index}`).type(candidate.lastName);   // Wymaga selektorów z indeksem

            // Dodanie testowego pliku (symulacja uploadu)
            // cy.get(candidate.photoFieldSelector).selectFile({
            //     contents: Cypress.Buffer.from('test data'), 
            //     fileName: `photo_${index}.jpg`,
            //     mimeType: 'image/jpeg',
            // }, { force: true });
        });

        cy.log('Krok 6: Oczekiwanie na POST do /api/create_Voting');
        cy.intercept('POST', '/api/create_Voting').as('createVotingRequest');

        cy.get('button:contains("Utwórz")').click();

        cy.wait('@createVotingRequest', { timeout: 10000 }).then((interception) => {
            expect(interception.response.statusCode).to.eq(201);
            expect(interception.response.body).to.have.property('success', true);
            expect(interception.response.body).to.have.property('id_glosowania').and.to.be.a('string');
            
            createdVotingId = interception.response.body.id_glosowania;
            cy.log(`Utworzone głosowanie ID: ${createdVotingId}`);
        });

        cy.log('Krok 9: Weryfikacja przekierowania na stronę głosowania');
        cy.url().should('include', '/voting/');
        cy.url().should('include', createdVotingId.toString());

        cy.get('h1').should('contain', votingName);
    });
});