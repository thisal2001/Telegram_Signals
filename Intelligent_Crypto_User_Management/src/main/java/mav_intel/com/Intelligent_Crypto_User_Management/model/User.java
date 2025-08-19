package mav_intel.com.Intelligent_Crypto_User_Management.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Data
@Table(name = "users")
@NoArgsConstructor
@AllArgsConstructor
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id")
    private Long id;

    @Column(name="username",unique = true,nullable=false)
    private String username;
    @Column(name="password",nullable=false)
    private String password;
    @Enumerated(EnumType.STRING)
    @Column(name = "role",nullable=false)
    private Role role;
}
